from rest_framework.serializers import ModelSerializer, Serializer, ListField, DictField, CharField, IntegerField
from rest_framework import serializers

from cart.models import CartItem, Cart
from product.serializers import ProductReadSerializer


class CartItemCreateSerializer(ModelSerializer):

    is_checked_out = serializers.BooleanField(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'is_checked_out']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None
        if user and user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=user)
            product = validated_data['product']
            quantity = validated_data.get('quantity', 1)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, product=product, defaults={'quantity': quantity}
            )
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            cart.update_total()
            return cart_item
        return super().create(validated_data)


class CartItemReadOnlySerializer(ModelSerializer):
    product = ProductReadSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'is_checked_out']
        read_only_fields = fields


class CartSerializer(ModelSerializer):
    items = CartItemReadOnlySerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'date_added', 'total', 'items']
