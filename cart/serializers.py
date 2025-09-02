from rest_framework.serializers import ModelSerializer, Serializer, ListField, DictField, CharField, IntegerField
from rest_framework import serializers

from cart.models import CartItem, Cart
from Products.models import Product, ProductImages
from Products.serializers import ProductSerializer
from Products.serializers import ProductImageSerializer
from category.serializers import CategorySerializer


class CartItemSerializer(ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'is_checked_out']


class CartSerializer(ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'date_added', 'total', 'item_count']

    def get_item_count(self, obj):
        return obj.items.filter(is_checked_out=False).count()


class BulkOperationSerializer(Serializer):
    """Serializer for individual bulk operations"""
    product_id = IntegerField()
    action = CharField(max_length=20)  # 'update_quantity' or 'remove'
    quantity = IntegerField(required=False, min_value=1)

    def validate(self, data):
        if data['action'] == 'update_quantity' and 'quantity' not in data:
            raise serializers.ValidationError(
                "Quantity is required for update_quantity action"
            )
        return data


class BulkCartOperationSerializer(Serializer):
    """Serializer for bulk cart operations"""
    operations = ListField(
        child=BulkOperationSerializer(),
        min_length=1,
        max_length=50  # Limit bulk operations to prevent abuse
    )
