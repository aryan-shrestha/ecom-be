from django.db import models
from django.utils import timezone

from product.models import Product, ProductVariant


class Warehouse(models.Model):
    """Multiple warehouse support"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Warehouse'
        verbose_name_plural = 'Warehouses'


class ProductInventory(models.Model):
    """Inventory tracking for products and variants"""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='inventory')
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name='inventory')
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name='inventory')

    quantity_available = models.PositiveIntegerField(default=0)
    quantity_reserved = models.PositiveIntegerField(
        default=0)  # Reserved during checkout
    quantity_sold = models.PositiveIntegerField(default=0)

    # Reorder management
    reorder_level = models.PositiveIntegerField(default=10)
    reorder_quantity = models.PositiveIntegerField(default=50)

    # Tracking
    last_restocked = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'variant', 'warehouse')
        verbose_name = 'Product Inventory'
        verbose_name_plural = 'Product Inventories'

    @property
    def quantity_on_hand(self):
        """Total quantity including reserved"""
        return self.quantity_available + self.quantity_reserved

    @property
    def needs_reorder(self):
        """Check if stock is below reorder level"""
        return self.quantity_available <= self.reorder_level

    def __str__(self):
        variant_info = f" - {self.variant.name}" if self.variant else ""
        return f"{self.product.name}{variant_info} @ {self.warehouse.name}"


class InventoryTransaction(models.Model):
    """Track all inventory movements"""
    TRANSACTION_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('RESERVE', 'Reserved'),
        ('RELEASE', 'Released'),
        ('ADJUSTMENT', 'Adjustment'),
        ('DAMAGED', 'Damaged'),
        ('RETURNED', 'Returned'),
    ]

    inventory = models.ForeignKey(
        ProductInventory, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(
        max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()  # Can be negative for OUT transactions
    # Order ID, PO Number, etc.
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # User who made the transaction
    created_by = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.inventory} - {self.transaction_type} - {self.quantity}"

    class Meta:
        verbose_name = 'Inventory Transaction'
        verbose_name_plural = 'Inventory Transactions'
        ordering = ['-created_at']
