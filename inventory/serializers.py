from rest_framework import serializers
from django.db import models
from .models import Warehouse, ProductInventory, InventoryTransaction
from product.serializers import ProductListSerializer, ProductVariantSerializer


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'code', 'address', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductInventorySerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    warehouse = WarehouseSerializer(read_only=True)
    quantity_on_hand = serializers.ReadOnlyField()
    needs_reorder = serializers.ReadOnlyField()

    class Meta:
        model = ProductInventory
        fields = ['id', 'product', 'variant', 'warehouse', 'quantity_available',
                  'quantity_reserved', 'quantity_sold', 'quantity_on_hand',
                  'reorder_level', 'reorder_quantity', 'needs_reorder',
                  'last_restocked', 'created_at', 'modified_at']
        read_only_fields = ['id', 'quantity_on_hand', 'needs_reorder',
                            'created_at', 'modified_at']


class ProductInventoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInventory
        fields = ['id', 'product', 'variant', 'warehouse', 'quantity_available',
                  'quantity_reserved', 'quantity_sold', 'reorder_level',
                  'reorder_quantity', 'last_restocked']
        read_only_fields = ['id']


class ProductInventoryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInventory
        fields = ['quantity_available', 'quantity_reserved', 'quantity_sold',
                  'reorder_level', 'reorder_quantity', 'last_restocked']


class InventoryTransactionSerializer(serializers.ModelSerializer):
    inventory = ProductInventorySerializer(read_only=True)

    class Meta:
        model = InventoryTransaction
        fields = ['id', 'inventory', 'transaction_type', 'quantity',
                  'reference_number', 'notes', 'created_at', 'created_by']
        read_only_fields = ['id', 'created_at']


class InventoryTransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryTransaction
        fields = ['inventory', 'transaction_type', 'quantity', 'reference_number',
                  'notes', 'created_by']

    def create(self, validated_data):
        transaction = InventoryTransaction.objects.create(**validated_data)

        # Update inventory quantities based on transaction type
        inventory = transaction.inventory
        quantity = transaction.quantity

        if transaction.transaction_type == 'IN':
            inventory.quantity_available += quantity
        elif transaction.transaction_type == 'OUT':
            inventory.quantity_available -= quantity
            inventory.quantity_sold += abs(quantity)
        elif transaction.transaction_type == 'RESERVE':
            inventory.quantity_available -= quantity
            inventory.quantity_reserved += quantity
        elif transaction.transaction_type == 'RELEASE':
            inventory.quantity_reserved -= quantity
            inventory.quantity_available += quantity
        elif transaction.transaction_type == 'ADJUSTMENT':
            inventory.quantity_available += quantity
        elif transaction.transaction_type == 'RETURNED':
            inventory.quantity_available += quantity
            inventory.quantity_sold -= abs(quantity)
        elif transaction.transaction_type == 'DAMAGED':
            inventory.quantity_available -= quantity

        inventory.save()
        return transaction


class InventoryStockUpdateSerializer(serializers.Serializer):
    """Serializer for bulk stock updates"""
    inventory_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    transaction_type = serializers.ChoiceField(
        choices=InventoryTransaction.TRANSACTION_TYPES)
    reference_number = serializers.CharField(max_length=100, required=False)
    notes = serializers.CharField(required=False)
    created_by = serializers.CharField(max_length=100, required=False)


class WarehouseInventorySerializer(serializers.ModelSerializer):
    """Serializer for warehouse inventory overview"""
    total_products = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    low_stock_items = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'code', 'address', 'is_active',
                  'total_products', 'total_quantity', 'low_stock_items']

    def get_total_products(self, obj):
        return obj.inventory.count()

    def get_total_quantity(self, obj):
        return sum(inv.quantity_available for inv in obj.inventory.all())

    def get_low_stock_items(self, obj):
        return obj.inventory.filter(quantity_available__lte=models.F('reorder_level')).count()


class ProductInventoryDetailSerializer(serializers.ModelSerializer):
    """Detailed inventory with recent transactions"""
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    warehouse = WarehouseSerializer(read_only=True)
    recent_transactions = serializers.SerializerMethodField()
    quantity_on_hand = serializers.ReadOnlyField()
    needs_reorder = serializers.ReadOnlyField()

    class Meta:
        model = ProductInventory
        fields = ['id', 'product', 'variant', 'warehouse', 'quantity_available',
                  'quantity_reserved', 'quantity_sold', 'quantity_on_hand',
                  'reorder_level', 'reorder_quantity', 'needs_reorder',
                  'last_restocked', 'recent_transactions', 'created_at', 'modified_at']

    def get_recent_transactions(self, obj):
        recent = obj.transactions.all()[:5]
        return InventoryTransactionSerializer(recent, many=True).data
