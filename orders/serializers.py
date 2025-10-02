from rest_framework import serializers

from cart.serializers import ProductReadSerializer
from .models import Payment, Order, OrderItem


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['payment_id', 'payment_method',
                  'amount_paid', 'status', 'created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductReadSerializer()

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'ordered']


class OrderSerializer(serializers.ModelSerializer):
    payment = PaymentSerializer()
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['payment', 'order_number', 'first_name',
                  'last_name', 'phone_no', 'email', 'address_line_1', 'address_line_2',
                  'order_note', 'vat', 'status', 'is_ordered', 'created_at', 'updated_at', 'items']
