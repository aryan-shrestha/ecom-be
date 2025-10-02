from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import DiscountRule, ProductDiscount, BulkPricingTier


# Inline classes
class ProductDiscountInline(admin.TabularInline):
    model = ProductDiscount
    extra = 0
    autocomplete_fields = ['product']


class BulkPricingTierInline(admin.TabularInline):
    model = BulkPricingTier
    extra = 0
    fields = ('min_quantity', 'max_quantity',
              'discount_percentage', 'fixed_price', 'is_active')


@admin.register(DiscountRule)
class DiscountRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_type', 'discount_value_display', 'apply_to',
                    'status_display', 'usage_display', 'validity_period', 'products_count']
    list_filter = ['discount_type', 'apply_to',
                   'is_active', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'modified_at',
                       'current_uses', 'discount_summary', 'usage_analytics']
    inlines = [ProductDiscountInline]
    date_hierarchy = 'start_date'

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'discount_type', 'discount_value', 'apply_to')
        }),
        ('Conditions', {
            'fields': ('minimum_quantity', 'minimum_amount', 'maximum_uses', 'current_uses')
        }),
        ('Validity', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('Analytics', {
            'fields': ('discount_summary', 'usage_analytics'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',)
        }),
    )

    def discount_value_display(self, obj):
        if obj.discount_type == 'PERCENTAGE':
            return format_html('<span style="color: green; font-weight: bold;">{}%</span>', obj.discount_value)
        elif obj.discount_type == 'FIXED':
            return format_html('<span style="color: blue; font-weight: bold;">${}</span>', obj.discount_value)
        else:  # BOGO
            return format_html('<span style="color: purple; font-weight: bold;">BOGO</span>')
    discount_value_display.short_description = 'Discount Value'

    def status_display(self, obj):
        now = timezone.now()
        if not obj.is_active:
            return format_html('<span style="color: gray;">Disabled</span>')
        elif now < obj.start_date:
            return format_html('<span style="color: orange;">Scheduled</span>')
        elif now > obj.end_date:
            return format_html('<span style="color: red;">Expired</span>')
        elif obj.maximum_uses and obj.current_uses >= obj.maximum_uses:
            return format_html('<span style="color: red;">Limit Reached</span>')
        else:
            return format_html('<span style="color: green; font-weight: bold;">Active</span>')
    status_display.short_description = 'Status'

    def usage_display(self, obj):
        if obj.maximum_uses:
            percentage = (obj.current_uses / obj.maximum_uses) * 100
            color = "red" if percentage >= 90 else "orange" if percentage >= 70 else "green"
            return format_html(
                '<span style="color: {};">{}/{} ({}%)</span>',
                color, obj.current_uses, obj.maximum_uses, int(percentage)
            )
        return f"{obj.current_uses} times"
    usage_display.short_description = 'Usage'

    def validity_period(self, obj):
        start = obj.start_date.strftime('%m/%d/%Y')
        end = obj.end_date.strftime('%m/%d/%Y')
        now = timezone.now()

        if now < obj.start_date:
            days_until = (obj.start_date.date() - now.date()).days
            return format_html('{} - {} <br><small style="color: orange;">Starts in {} days</small>', start, end, days_until)
        elif now > obj.end_date:
            days_ago = (now.date() - obj.end_date.date()).days
            return format_html('{} - {} <br><small style="color: red;">Expired {} days ago</small>', start, end, days_ago)
        else:
            days_left = (obj.end_date.date() - now.date()).days
            return format_html('{} - {} <br><small style="color: green;">{} days remaining</small>', start, end, days_left)
    validity_period.short_description = 'Validity Period'

    def products_count(self, obj):
        if obj.apply_to == 'PRODUCT':
            count = obj.products.count()
            if count > 0:
                url = reverse('admin:discount_productdiscount_changelist')
                return format_html('<a href="{}?discount_rule__id__exact={}">{} products</a>', url, obj.id, count)
            return "0 products"
        else:
            return f"All {obj.apply_to.lower()} products"
    products_count.short_description = 'Applicable Products'

    def discount_summary(self, obj):
        if obj.id:
            now = timezone.now()
            is_valid = obj.is_valid()

            summary = f"""
            <div style="background: #f0f8ff; padding: 15px; border-radius: 8px; border-left: 4px solid #007cba;">
                <h4 style="margin-top: 0;">Discount Rule Summary</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div>
                        <strong>Type:</strong> {obj.get_discount_type_display()}<br>
                        <strong>Value:</strong> {obj.discount_value}<br>
                        <strong>Applies to:</strong> {obj.get_apply_to_display()}<br>
                        <strong>Status:</strong> <span style="color: {'green' if is_valid else 'red'};">{'Active' if is_valid else 'Inactive'}</span>
                    </div>
                    <div>
                        <strong>Min Quantity:</strong> {obj.minimum_quantity}<br>
                        <strong>Min Amount:</strong> ${obj.minimum_amount}<br>
                        <strong>Usage Limit:</strong> {obj.maximum_uses or 'Unlimited'}<br>
                        <strong>Current Usage:</strong> {obj.current_uses}
                    </div>
                </div>
            </div>
            """
            return mark_safe(summary)
        return "Save to see summary"
    discount_summary.short_description = 'Discount Summary'

    def usage_analytics(self, obj):
        if obj.id and obj.current_uses > 0:
            # Calculate some basic analytics
            days_active = max(
                1, (timezone.now().date() - obj.start_date.date()).days)
            avg_daily_usage = obj.current_uses / days_active

            if obj.maximum_uses:
                remaining_uses = obj.maximum_uses - obj.current_uses
                estimated_days_to_limit = remaining_uses / \
                    avg_daily_usage if avg_daily_usage > 0 else float('inf')
            else:
                estimated_days_to_limit = float('inf')

            analytics = f"""
            <div style="background: #f8f8f8; padding: 15px; border-radius: 8px;">
                <h4 style="margin-top: 0;">Usage Analytics</h4>
                <ul style="margin: 0; padding-left: 20px;">
                    <li><strong>Days Active:</strong> {days_active}</li>
                    <li><strong>Average Daily Usage:</strong> {avg_daily_usage:.1f}</li>
                    <li><strong>Total Uses:</strong> {obj.current_uses}</li>
                    {f'<li><strong>Remaining Uses:</strong> {obj.maximum_uses - obj.current_uses}</li>' if obj.maximum_uses else ''}
                    {f'<li><strong>Est. Days to Limit:</strong> {int(estimated_days_to_limit) if estimated_days_to_limit != float("inf") else "N/A"}</li>' if obj.maximum_uses else ''}
                </ul>
            </div>
            """
            return mark_safe(analytics)
        return "No usage data available"
    usage_analytics.short_description = 'Usage Analytics'


@admin.register(ProductDiscount)
class ProductDiscountAdmin(admin.ModelAdmin):
    list_display = ['product', 'discount_rule_display',
                    'discount_value', 'status_display', 'validity_period']
    list_filter = ['discount_rule__discount_type',
                   'discount_rule__is_active', 'discount_rule__apply_to']
    search_fields = ['product__name', 'discount_rule__name']
    autocomplete_fields = ['product', 'discount_rule']

    def discount_rule_display(self, obj):
        return f"{obj.discount_rule.name} ({obj.discount_rule.get_discount_type_display()})"
    discount_rule_display.short_description = 'Discount Rule'

    def discount_value(self, obj):
        rule = obj.discount_rule
        if rule.discount_type == 'PERCENTAGE':
            return format_html('<span style="color: green; font-weight: bold;">{}%</span>', rule.discount_value)
        elif rule.discount_type == 'FIXED':
            return format_html('<span style="color: blue; font-weight: bold;">${}</span>', rule.discount_value)
        else:
            return format_html('<span style="color: purple; font-weight: bold;">BOGO</span>')
    discount_value.short_description = 'Discount Value'

    def status_display(self, obj):
        now = timezone.now()
        rule = obj.discount_rule
        if not rule.is_active:
            return format_html('<span style="color: gray;">Disabled</span>')
        elif now < rule.start_date:
            return format_html('<span style="color: orange;">Scheduled</span>')
        elif now > rule.end_date:
            return format_html('<span style="color: red;">Expired</span>')
        else:
            return format_html('<span style="color: green; font-weight: bold;">Active</span>')
    status_display.short_description = 'Status'

    def validity_period(self, obj):
        rule = obj.discount_rule
        start = rule.start_date.strftime('%m/%d/%Y')
        end = rule.end_date.strftime('%m/%d/%Y')
        return f"{start} - {end}"
    validity_period.short_description = 'Valid Period'


@admin.register(BulkPricingTier)
class BulkPricingTierAdmin(admin.ModelAdmin):
    list_display = ['product_display', 'variant_display',
                    'quantity_range', 'pricing_display', 'savings_display', 'is_active']
    list_filter = ['is_active', 'created_at', 'product__category']
    search_fields = ['product__name', 'variant__name', 'variant__sku']
    readonly_fields = ['created_at', 'pricing_summary']
    autocomplete_fields = ['product', 'variant']

    fieldsets = (
        ('Product Information', {
            'fields': ('product', 'variant')
        }),
        ('Quantity Range', {
            'fields': ('min_quantity', 'max_quantity')
        }),
        ('Pricing', {
            'fields': ('discount_percentage', 'fixed_price', 'is_active')
        }),
        ('Summary', {
            'fields': ('pricing_summary',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def product_display(self, obj):
        return f"{obj.product.name}"
    product_display.short_description = 'Product'

    def variant_display(self, obj):
        if obj.variant:
            return f"{obj.variant.name} ({obj.variant.sku})"
        return "All variants"
    variant_display.short_description = 'Variant'

    def quantity_range(self, obj):
        if obj.max_quantity:
            return f"{obj.min_quantity} - {obj.max_quantity}"
        return f"{obj.min_quantity}+"
    quantity_range.short_description = 'Quantity Range'

    def pricing_display(self, obj):
        if obj.discount_percentage:
            return format_html('<span style="color: green; font-weight: bold;">{}% off</span>', obj.discount_percentage)
        elif obj.fixed_price:
            return format_html('<span style="color: blue; font-weight: bold;">${} each</span>', obj.fixed_price)
        return "-"
    pricing_display.short_description = 'Pricing'

    def savings_display(self, obj):
        if obj.product:
            base_price = obj.product.price
            if obj.variant:
                base_price = obj.variant.final_price

            bulk_price = obj.get_price(base_price)
            savings = base_price - bulk_price

            if savings > 0:
                savings_percent = (savings / base_price) * 100
                return format_html(
                    '<span style="color: green;">${:.2f} ({}%)</span>',
                    savings, int(savings_percent)
                )
            return "No savings"
        return "-"
    savings_display.short_description = 'Savings per Unit'

    def pricing_summary(self, obj):
        if obj.id and obj.product:
            base_price = obj.product.price
            if obj.variant:
                base_price = obj.variant.final_price

            bulk_price = obj.get_price(base_price)
            savings_per_unit = base_price - bulk_price
            min_qty_savings = savings_per_unit * obj.min_quantity

            summary = f"""
            <div style="background: #f0f8ff; padding: 15px; border-radius: 8px;">
                <h4 style="margin-top: 0;">Pricing Summary</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div>
                        <strong>Base Price:</strong> ${base_price:.2f}<br>
                        <strong>Bulk Price:</strong> ${bulk_price:.2f}<br>
                        <strong>Savings per Unit:</strong> ${savings_per_unit:.2f}<br>
                        <strong>Quantity Range:</strong> {obj.min_quantity}{f" - {obj.max_quantity}" if obj.max_quantity else "+"}
                    </div>
                    <div>
                        <strong>Min Order Savings:</strong> ${min_qty_savings:.2f}<br>
                        <strong>Discount Type:</strong> {"Percentage" if obj.discount_percentage else "Fixed Price"}<br>
                        <strong>Status:</strong> <span style="color: {'green' if obj.is_active else 'red'};">{'Active' if obj.is_active else 'Inactive'}</span>
                    </div>
                </div>
            </div>
            """
            return mark_safe(summary)
        return "Save to see pricing summary"
    pricing_summary.short_description = 'Pricing Summary'
