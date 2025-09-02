from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication

from Products.models import Product
from cart.models import Cart, CartItem
from cart.serializers import CartItemSerializer, CartSerializer, BulkCartOperationSerializer

# Create your views here.


def get_session_id(request):
    """Get or create session ID for anonymous users"""
    session_id = request.session.session_key
    if session_id == None:
        request.session.save()
        session_id = request.session.session_key
    return session_id


def get_or_create_cart(request):
    """Get or create cart for authenticated or anonymous users"""
    if request.user.is_authenticated:
        # For authenticated users, try to get anonymous cart and assign user to it
        try:
            anonymous_session_key = request.session.get('cart_session_key')
            if anonymous_session_key:
                cart = Cart.objects.get(
                    session_key=anonymous_session_key, user__isnull=True)
                # Assign user to the cart and update session key
                cart.user = request.user
                cart.session_key = get_session_id(request)
                cart.save()
            else:
                # No anonymous cart session key, check if user already has a cart
                cart = Cart.objects.filter(user=request.user).first()
                if not cart:
                    # Create new cart for user
                    session_key = get_session_id(request)
                    cart = Cart.objects.create(
                        user=request.user,
                        session_key=session_key
                    )
        except Cart.DoesNotExist:
            # Anonymous cart doesn't exist, check if user already has a cart
            cart = Cart.objects.filter(user=request.user).first()
            if not cart:
                # Create new cart for user
                session_key = get_session_id(request)
                cart = Cart.objects.create(
                    user=request.user,
                    session_key=session_key
                )
    else:
        # For anonymous users, use session-based cart
        session_key = get_session_id(request)
        cart, _ = Cart.objects.get_or_create(
            session_key=session_key,
            user__isnull=True
        )

    # Update session data with current cart's session key
    request.session['cart_session_key'] = cart.session_key
    request.session.save()
    return cart


def validate_inventory(product, quantity):
    """Validate if requested quantity is available"""
    # Assuming Product model has a stock field
    if hasattr(product, 'stock') and product.stock < quantity:
        raise serializers.ValidationError(
            f"Only {product.stock} items available for {product.name}"
        )
    return True


def clean_expired_carts():
    """Remove carts older than 30 days"""
    expiry_date = timezone.now().date() - timedelta(days=30)
    Cart.objects.filter(date_added__lt=expiry_date, user__isnull=True).delete()


class CartViewSet(viewsets.ModelViewSet):
    """
    ViewSet for cart operations with comprehensive functionality.
    Supports both authenticated and anonymous users.
    """
    serializer_class = CartSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Get cart based on user authentication status"""
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user)
        else:
            session_key = get_session_id(self.request)
            return Cart.objects.filter(session_key=session_key)

    def get_object(self):
        """Get or create cart for current user/session"""
        return get_or_create_cart(self.request)

    @action(detail=False, methods=['get'])
    def details(self, request):
        """Get cart details with items"""
        # Clean expired carts periodically
        clean_expired_carts()

        cart = self.get_object()
        cart_serializer = self.get_serializer(cart)

        cart_items = CartItem.objects.filter(cart=cart, is_checked_out=False)

        cart_items_serializer = CartItemSerializer(cart_items, many=True)
        return Response({
            "cart": cart_serializer.data,
            "cart_items": cart_items_serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='add-item')
    def add_item(self, request):
        """Add item to cart with inventory validation"""
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate inventory
        try:
            validate_inventory(product, quantity)
        except serializers.ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart = self.get_object()
        cart_item, _ = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 0}
        )
        cart_item.quantity += quantity
        cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response({
            'cart_item': serializer.data,
            'cart_total': cart.total
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['patch'])
    def update_item(self, request):
        """Update item quantity (increase/decrease)"""
        operation = request.data.get('operation')
        product_id = request.data.get('product_id')

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'detail': 'Product does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )

        cart = self.get_object()
        cart_item = CartItem.objects.filter(cart=cart, product=product).first()

        if not cart_item:
            return Response(
                {'detail': 'Item not found in the cart'},
                status=status.HTTP_404_NOT_FOUND
            )

        if operation == 'increase':
            try:
                validate_inventory(product, cart_item.quantity + 1)
            except serializers.ValidationError as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.quantity += 1
        elif operation == 'decrease':
            if cart_item.quantity <= 1:
                cart_item.delete()
                return Response(
                    {'detail': 'Item removed from cart', 'cart_total': cart.total},
                    status=status.HTTP_204_NO_CONTENT
                )
            else:
                cart_item.quantity -= 1
        else:
            return Response(
                {'detail': 'Invalid operation. Use "increase" or "decrease"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.save()
        serializer = CartItemSerializer(cart_item)
        return Response({
            'cart_item': serializer.data,
            'cart_total': cart.total
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'])
    def remove_item(self, request):
        """Remove specific item from cart"""
        product_id = request.data.get('product_id')

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'detail': 'Product does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )

        cart = self.get_object()
        cart_item = CartItem.objects.filter(cart=cart, product=product).first()

        if not cart_item:
            return Response(
                {'detail': 'Item not found in the cart'},
                status=status.HTTP_404_NOT_FOUND
            )

        cart_item.delete()
        return Response({
            'detail': 'Item removed from cart',
            'cart_total': cart.total
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear all items from cart"""
        cart = self.get_object()
        cart.items.filter(is_checked_out=False).delete()
        return Response({
            'detail': 'Cart cleared successfully',
            'cart_total': cart.total
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update multiple cart items"""
        serializer = BulkCartOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        cart = self.get_object()
        operations = serializer.validated_data['operations']
        results = []

        for operation in operations:
            try:
                product = Product.objects.get(id=operation['product_id'])
                cart_item = CartItem.objects.filter(
                    cart=cart, product=product).first()

                if operation['action'] == 'update_quantity':
                    if cart_item:
                        validate_inventory(product, operation['quantity'])
                        cart_item.quantity = operation['quantity']
                        cart_item.save()
                        results.append({
                            'product_id': product.id,
                            'status': 'updated',
                            'quantity': cart_item.quantity
                        })
                    else:
                        results.append({
                            'product_id': product.id,
                            'status': 'not_found'
                        })

                elif operation['action'] == 'remove':
                    if cart_item:
                        cart_item.delete()
                        results.append({
                            'product_id': product.id,
                            'status': 'removed'
                        })
                    else:
                        results.append({
                            'product_id': product.id,
                            'status': 'not_found'
                        })

            except Product.DoesNotExist:
                results.append({
                    'product_id': operation['product_id'],
                    'status': 'product_not_found'
                })
            except serializers.ValidationError as e:
                results.append({
                    'product_id': operation['product_id'],
                    'status': 'error',
                    'error': str(e)
                })

        return Response({
            'results': results,
            'cart_total': cart.total
        }, status=status.HTTP_200_OK)
