from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from .models import Warehouse, ProductInventory, InventoryTransaction


# Inline classes
class ProductInventoryInline(admin.TabularInline):
    model = ProductInventory
    extra = 0
    readonly_fields = ('quantity_on_hand', 'needs_reorder_display')
    fields = ('product', 'variant', 'quantity_available', 'quantity_reserved',
              'quantity_on_hand', 'reorder_level', 'needs_reorder_display')

    def needs_reorder_display(self, obj):
        if obj.needs_reorder:
            return format_html('<span style="color: red; font-weight: bold;">⚠ YES</span>')
        return format_html('<span style="color: green;">✓ No</span>')
    needs_reorder_display.short_description = 'Reorder?'


class InventoryTransactionInline(admin.TabularInline):
    model = InventoryTransaction
    extra = 0
    readonly_fields = ('created_at', 'created_by')
    fields = ('transaction_type', 'quantity', 'reference_number',
              'notes', 'created_by', 'created_at')
    ordering = ('-created_at',)

    def has_change_permission(self, request, obj=None):
        return False  # Prevent editing for audit trail


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'total_products',
                    'total_stock', 'low_stock_items', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'address']
    readonly_fields = ['created_at', 'inventory_summary']
    inlines = [ProductInventoryInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'is_active')
        }),
        ('Address', {
            'fields': ('address',)
        }),
        ('Statistics', {
            'fields': ('inventory_summary',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def total_products(self, obj):
        count = obj.inventory.count()
        if count > 0:
            url = reverse('admin:inventory_productinventory_changelist')
            return format_html('<a href="{}?warehouse__id__exact={}">{}</a>', url, obj.id, count)
        return 0
    total_products.short_description = 'Products'

    def total_stock(self, obj):
        total = obj.inventory.aggregate(
            total=Sum('quantity_available')
        )['total'] or 0
        return f"{total:,}"
    total_stock.short_description = 'Total Stock'

    def low_stock_items(self, obj):
        from django.db.models import F
        count = obj.inventory.filter(
            quantity_available__lte=F('reorder_level')).count()
        if count > 0:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', count)
        return format_html('<span style="color: green;">0</span>')
    low_stock_items.short_description = 'Low Stock'

    def inventory_summary(self, obj):
        if obj.id:
            from django.db.models import F
            inventory = obj.inventory.all()
            total_items = inventory.count()
            total_stock = inventory.aggregate(
                total=Sum('quantity_available'))['total'] or 0
            total_reserved = inventory.aggregate(
                total=Sum('quantity_reserved'))['total'] or 0
            low_stock = inventory.filter(
                quantity_available__lte=F('reorder_level')).count()
            out_of_stock = inventory.filter(quantity_available=0).count()

            summary = f"""
            <div style="background: #f8f8f8; padding: 10px; border-radius: 5px;">
                <h4>Inventory Summary</h4>
                <ul>
                    <li><strong>Total Products:</strong> {total_items}</li>
                    <li><strong>Total Stock:</strong> {total_stock:,} units</li>
                    <li><strong>Reserved Stock:</strong> {total_reserved:,} units</li>
                    <li><strong>Low Stock Items:</strong> <span style="color: red;">{low_stock}</span></li>
                    <li><strong>Out of Stock:</strong> <span style="color: red;">{out_of_stock}</span></li>
                </ul>
            </div>
            """
            return mark_safe(summary)
        return "Save to see summary"
    inventory_summary.short_description = 'Inventory Summary'


@admin.register(ProductInventory)
class ProductInventoryAdmin(admin.ModelAdmin):
    list_display = ['product_display', 'variant_display', 'warehouse', 'stock_status',
                    'quantity_available', 'quantity_reserved', 'needs_reorder_display', 'last_transaction']
    list_filter = ['warehouse', 'created_at', 'last_restocked']
    search_fields = ['product__name', 'variant__name',
                     'variant__sku', 'warehouse__name']
    readonly_fields = ['created_at', 'modified_at',
                       'quantity_on_hand', 'stock_summary', 'recent_transactions']
    autocomplete_fields = ['product', 'variant', 'warehouse']
    inlines = [InventoryTransactionInline]

    fieldsets = (
        ('Product Information', {
            'fields': ('product', 'variant', 'warehouse')
        }),
        ('Stock Levels', {
            'fields': ('quantity_available', 'quantity_reserved', 'quantity_sold', 'quantity_on_hand')
        }),
        ('Reorder Management', {
            'fields': ('reorder_level', 'reorder_quantity', 'last_restocked')
        }),
        ('Summary', {
            'fields': ('stock_summary',),
            'classes': ('collapse',)
        }),
        ('Recent Activity', {
            'fields': ('recent_transactions',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',)
        }),
    )

    def product_display(self, obj):
        return f"{obj.product.name}"
    product_display.short_description = 'Product'

    def variant_display(self, obj):
        if obj.variant:
            return f"{obj.variant.name} ({obj.variant.sku})"
        return "-"
    variant_display.short_description = 'Variant'

    def stock_status(self, obj):
        if obj.quantity_available == 0:
            return format_html('<span style="color: red; font-weight: bold;">Out of Stock</span>')
        elif obj.needs_reorder:
            return format_html('<span style="color: orange; font-weight: bold;">Low Stock</span>')
        else:
            return format_html('<span style="color: green;">In Stock</span>')
    stock_status.short_description = 'Status'

    def needs_reorder_display(self, obj):
        if obj.needs_reorder:
            return format_html('<span style="color: red; font-weight: bold;">⚠ YES</span>')
        return format_html('<span style="color: green;">✓ No</span>')
    needs_reorder_display.short_description = 'Reorder?'

    def last_transaction(self, obj):
        last = obj.transactions.first()
        if last:
            return f"{last.transaction_type} ({last.quantity}) - {last.created_at.strftime('%m/%d/%Y')}"
        return "No transactions"
    last_transaction.short_description = 'Last Transaction'

    def stock_summary(self, obj):
        if obj.id:
            summary = f"""
            <div style="background: #f0f8ff; padding: 10px; border-radius: 5px;">
                <h4>Stock Summary</h4>
                <ul>
                    <li><strong>Available:</strong> {obj.quantity_available:,} units</li>
                    <li><strong>Reserved:</strong> {obj.quantity_reserved:,} units</li>
                    <li><strong>On Hand:</strong> {obj.quantity_on_hand:,} units</li>
                    <li><strong>Sold:</strong> {obj.quantity_sold:,} units</li>
                    <li><strong>Reorder Level:</strong> {obj.reorder_level:,} units</li>
                    <li><strong>Status:</strong> {'Low Stock' if obj.needs_reorder else 'Adequate'}</li>
                </ul>
            </div>
            """
            return mark_safe(summary)
        return "Save to see summary"
    stock_summary.short_description = 'Stock Summary'

    def recent_transactions(self, obj):
        if obj.id:
            transactions = obj.transactions.all()[:5]
            if transactions:
                summary = "<div style='background: #f8f8f8; padding: 10px; border-radius: 5px;'>"
                summary += "<h4>Recent Transactions</h4><ul>"
                for trans in transactions:
                    color = "green" if trans.transaction_type == "IN" else "red" if trans.transaction_type == "OUT" else "blue"
                    summary += f"<li style='color: {color};'><strong>{trans.transaction_type}:</strong> {trans.quantity} units - {trans.created_at.strftime('%m/%d/%Y %H:%M')}</li>"
                summary += "</ul></div>"
                return mark_safe(summary)
            return "No transactions"
        return "Save to see transactions"
    recent_transactions.short_description = 'Recent Transactions'


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ['inventory_display', 'transaction_type', 'quantity_display',
                    'reference_number', 'created_by', 'created_at']
    list_filter = ['transaction_type', 'inventory__warehouse', 'created_at']
    search_fields = ['inventory__product__name',
                     'reference_number', 'notes', 'created_by']
    readonly_fields = ['created_at']
    autocomplete_fields = ['inventory']
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        ('Transaction Details', {
            'fields': ('inventory', 'transaction_type', 'quantity', 'reference_number')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def inventory_display(self, obj):
        product_name = obj.inventory.product.name
        variant_info = f" - {obj.inventory.variant.name}" if obj.inventory.variant else ""
        warehouse = obj.inventory.warehouse.code
        return f"{product_name}{variant_info} @ {warehouse}"
    inventory_display.short_description = 'Inventory Item'

    def quantity_display(self, obj):
        color = "green" if obj.transaction_type == "IN" else "red" if obj.transaction_type == "OUT" else "blue"
        sign = "+" if obj.transaction_type == "IN" else "-" if obj.transaction_type == "OUT" else ""
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}</span>',
            color, sign, obj.quantity
        )
    quantity_display.short_description = 'Quantity'

    def has_change_permission(self, request, obj=None):
        # Prevent editing transactions after creation for audit purposes
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion for audit trail
        return False
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['inventory__product__name', 'reference_number', 'notes']
    readonly_fields = ['created_at']

    def has_change_permission(self, request, obj=None):
        # Prevent editing transactions after creation for audit purposes
        return False
