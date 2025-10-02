from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q

from backend.permissions import IsAdminOrReadOnly
from .models import DiscountRule, ProductDiscount, BulkPricingTier
from .serializers import (
    DiscountRuleSerializer, DiscountRuleCreateSerializer, ProductDiscountSerializer,
    ProductDiscountCreateSerializer, BulkPricingTierSerializer, BulkPricingTierCreateSerializer,
    ProductDiscountDetailSerializer, DiscountUsageSerializer, BulkPricingCalculatorSerializer
)


class DiscountRuleViewSet(viewsets.ModelViewSet):
    """Manage discount rules"""

    queryset = DiscountRule.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['discount_type', 'apply_to', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'start_date', 'end_date', 'created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DiscountRuleCreateSerializer
        return DiscountRuleSerializer

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get currently active discount rules"""
        now = timezone.now()
        active_discounts = self.get_queryset().filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )
        serializer = self.get_serializer(active_discounts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get discounts expiring in the next 7 days"""
        now = timezone.now()
        week_from_now = now + timezone.timedelta(days=7)

        expiring_discounts = self.get_queryset().filter(
            is_active=True,
            start_date__lte=now,
            end_date__lte=week_from_now,
            end_date__gte=now
        )
        serializer = self.get_serializer(expiring_discounts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def apply_to_products(self, request, pk=None):
        """Apply discount rule to multiple products"""
        discount_rule = self.get_object()
        product_ids = request.data.get('product_ids', [])

        if not product_ids:
            return Response({'error': 'product_ids required'},
                            status=status.HTTP_400_BAD_REQUEST)

        created_discounts = []
        for product_id in product_ids:
            discount, created = ProductDiscount.objects.get_or_create(
                discount_rule=discount_rule,
                product_id=product_id
            )
            if created:
                created_discounts.append(discount.id)

        return Response({
            'message': f'Applied discount to {len(created_discounts)} products',
            'created_discounts': created_discounts
        })

    @action(detail=True, methods=['post'])
    def increment_usage(self, request, pk=None):
        """Increment usage count for a discount rule"""
        discount_rule = self.get_object()

        if discount_rule.maximum_uses and discount_rule.current_uses >= discount_rule.maximum_uses:
            return Response({'error': 'Discount usage limit reached'},
                            status=status.HTTP_400_BAD_REQUEST)

        discount_rule.current_uses += 1
        discount_rule.save()

        serializer = self.get_serializer(discount_rule)
        return Response(serializer.data)


class ProductDiscountViewSet(viewsets.ModelViewSet):
    """Manage product-specific discounts"""

    queryset = ProductDiscount.objects.select_related(
        'discount_rule', 'product')
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['discount_rule', 'product', 'discount_rule__is_active']
    search_fields = ['product__name', 'discount_rule__name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductDiscountCreateSerializer
        return ProductDiscountSerializer

    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Get all discounts for a specific product"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({'error': 'product_id parameter required'},
                            status=status.HTTP_400_BAD_REQUEST)

        discounts = self.get_queryset().filter(product_id=product_id)
        serializer = self.get_serializer(discounts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def calculate_discount(self, request):
        """Calculate discount for a product"""
        serializer = DiscountUsageSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            try:
                discount_rule = DiscountRule.objects.get(
                    id=data['discount_rule_id'])
                from product.models import Product
                product = Product.objects.get(id=data['product_id'])
            except (DiscountRule.DoesNotExist, Product.DoesNotExist) as e:
                return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

            # Calculate discount
            quantity = data['quantity']
            base_price = float(product.price)
            total_before_discount = base_price * quantity

            if discount_rule.discount_type == 'PERCENTAGE':
                discount_amount = total_before_discount * \
                    (float(discount_rule.discount_value) / 100)
            elif discount_rule.discount_type == 'FIXED':
                discount_amount = float(
                    discount_rule.discount_value) * quantity
            else:  # BOGO
                free_items = quantity // 2
                discount_amount = base_price * free_items

            total_after_discount = total_before_discount - discount_amount

            return Response({
                'product_id': data['product_id'],
                'quantity': quantity,
                'base_price': base_price,
                'total_before_discount': total_before_discount,
                'discount_amount': discount_amount,
                'total_after_discount': total_after_discount,
                'discount_percentage': (discount_amount / total_before_discount * 100) if total_before_discount > 0 else 0
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BulkPricingTierViewSet(viewsets.ModelViewSet):
    """Manage bulk pricing tiers"""

    queryset = BulkPricingTier.objects.select_related('product', 'variant')
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['product', 'variant', 'is_active']
    search_fields = ['product__name', 'variant__name']
    ordering_fields = ['min_quantity', 'created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BulkPricingTierCreateSerializer
        return BulkPricingTierSerializer

    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Get bulk pricing tiers for a specific product"""
        product_id = request.query_params.get('product_id')
        variant_id = request.query_params.get('variant_id')

        if not product_id:
            return Response({'error': 'product_id parameter required'},
                            status=status.HTTP_400_BAD_REQUEST)

        tiers = self.get_queryset().filter(product_id=product_id, is_active=True)

        if variant_id:
            tiers = tiers.filter(variant_id=variant_id)

        tiers = tiers.order_by('min_quantity')
        serializer = self.get_serializer(tiers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def calculate_bulk_price(self, request):
        """Calculate bulk pricing for a product"""
        serializer = BulkPricingCalculatorSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            try:
                from product.models import Product, ProductVariant
                product = Product.objects.get(id=data['product_id'])
                variant = None

                if data.get('variant_id'):
                    variant = ProductVariant.objects.get(id=data['variant_id'])
                    base_price = variant.final_price
                else:
                    base_price = float(product.price)

            except (Product.DoesNotExist, ProductVariant.DoesNotExist) as e:
                return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

            quantity = data['quantity']

            # Find applicable bulk pricing tier
            tiers = BulkPricingTier.objects.filter(
                product=product,
                variant=variant,
                is_active=True,
                min_quantity__lte=quantity
            ).order_by('-min_quantity')

            if tiers.exists():
                applicable_tier = tiers.first()
                if applicable_tier.max_quantity is None or quantity <= applicable_tier.max_quantity:
                    bulk_price = applicable_tier.get_price(base_price)
                    total_price = bulk_price * quantity
                    savings = (base_price - bulk_price) * quantity

                    return Response({
                        'product_id': data['product_id'],
                        'variant_id': data.get('variant_id'),
                        'quantity': quantity,
                        'base_price': base_price,
                        'bulk_price': bulk_price,
                        'total_price': total_price,
                        'savings': savings,
                        'tier_id': applicable_tier.id,
                        'tier_min_quantity': applicable_tier.min_quantity
                    })

            # No bulk pricing applicable
            total_price = base_price * quantity
            return Response({
                'product_id': data['product_id'],
                'variant_id': data.get('variant_id'),
                'quantity': quantity,
                'base_price': base_price,
                'bulk_price': base_price,
                'total_price': total_price,
                'savings': 0,
                'tier_id': None,
                'message': 'No bulk pricing tier applicable'
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
