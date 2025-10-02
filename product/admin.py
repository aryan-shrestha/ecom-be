from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django import forms

from product.models import (
    Product, ProductAttribute, ProductAttributeValue,
    ProductVariant, ProductVariantAttribute
)


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'


# Inline classes for better UX
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    readonly_fields = ('final_price', 'created_at', 'modified_at')
    fields = ('sku', 'name', 'price_adjustment',
              'final_price', 'is_active', 'images')

    def final_price(self, obj):
        if obj.id:
            return f"${obj.final_price:.2f}"
        return "-"
    final_price.short_description = "Final Price"


class ProductVariantAttributeInline(admin.TabularInline):
    model = ProductVariantAttribute
    extra = 0
    autocomplete_fields = ['attribute_value']


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1
    fields = ('value', 'display_value', 'hex_color')


# Main Admin Classes
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('name', 'category', 'price',
                    'variants_count', 'created_at', 'is_active_display')
    list_filter = ('category', 'created_at', 'modified_at')
    search_fields = ('name', 'description', 'slug')
    readonly_fields = ('created_at', 'modified_at', 'variants_count')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductVariantInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'price', 'description')
        }),
        ('Media', {
            'fields': ('images',),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('variants_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',)
        }),
    )

    def variants_count(self, obj):
        if obj.id:
            count = obj.variants.count()
            url = reverse('admin:product_productvariant_changelist')
            return format_html(
                '<a href="{}?product__id__exact={}">{} variants</a>',
                url, obj.id, count
            )
        return 0
    variants_count.short_description = "Variants"

    def is_active_display(self, obj):
        # Check if product has active variants
        active_variants = obj.variants.filter(is_active=True).count()
        total_variants = obj.variants.count()

        if total_variants == 0:
            return format_html('<span style="color: orange;">No variants</span>')
        elif active_variants > 0:
            return format_html('<span style="color: green;">✓ Active ({}/{})</span>', active_variants, total_variants)
        else:
            return format_html('<span style="color: red;">✗ Inactive</span>')
    is_active_display.short_description = "Status"


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'is_required',
                    'values_count', 'created_at')
    list_filter = ('is_required', 'created_at')
    search_fields = ('name', 'display_name')
    readonly_fields = ('created_at', 'values_count')
    inlines = [ProductAttributeValueInline]

    def values_count(self, obj):
        if obj.id:
            count = obj.values.count()
            url = reverse('admin:product_productattributevalue_changelist')
            return format_html(
                '<a href="{}?attribute__id__exact={}">{} values</a>',
                url, obj.id, count
            )
        return 0
    values_count.short_description = "Values"


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value', 'display_value',
                    'hex_color_display', 'usage_count')
    list_filter = ('attribute',)
    search_fields = ('value', 'display_value', 'attribute__name')
    autocomplete_fields = ['attribute']
    readonly_fields = ('usage_count',)

    def hex_color_display(self, obj):
        if obj.hex_color:
            return format_html(
                '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; display: inline-block; margin-right: 5px;"></div>{}',
                obj.hex_color, obj.hex_color
            )
        return "-"
    hex_color_display.short_description = "Color"

    def usage_count(self, obj):
        if obj.id:
            count = ProductVariantAttribute.objects.filter(
                attribute_value=obj).count()
            if count > 0:
                url = reverse(
                    'admin:product_productvariantattribute_changelist')
                return format_html(
                    '<a href="{}?attribute_value__id__exact={}">Used in {} variants</a>',
                    url, obj.id, count
                )
            return "Not used"
        return 0
    usage_count.short_description = "Usage"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('sku', 'product', 'name', 'price_adjustment',
                    'final_price_display', 'is_active', 'attributes_display')
    list_filter = ('is_active', 'product__category', 'created_at')
    search_fields = ('sku', 'name', 'product__name')
    readonly_fields = ('final_price_display', 'created_at',
                       'modified_at', 'attributes_summary')
    autocomplete_fields = ['product']
    inlines = [ProductVariantAttributeInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('product', 'sku', 'name', 'is_active')
        }),
        ('Pricing', {
            'fields': ('price_adjustment', 'final_price_display')
        }),
        ('Media', {
            'fields': ('images',),
            'classes': ('collapse',)
        }),
        ('Attributes', {
            'fields': ('attributes_summary',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',)
        }),
    )

    def final_price_display(self, obj):
        if obj.id:
            return f"${obj.final_price:.2f}"
        return "-"
    final_price_display.short_description = "Final Price"

    def attributes_display(self, obj):
        if obj.id:
            attrs = obj.attributes.select_related(
                'attribute_value__attribute')[:3]
            attr_list = [
                f"{attr.attribute_value.attribute.name}: {attr.attribute_value.value}" for attr in attrs]
            if obj.attributes.count() > 3:
                attr_list.append(f"... +{obj.attributes.count() - 3} more")
            return ", ".join(attr_list) if attr_list else "No attributes"
        return "-"
    attributes_display.short_description = "Attributes"

    def attributes_summary(self, obj):
        if obj.id:
            attrs = obj.attributes.select_related('attribute_value__attribute')
            if attrs:
                summary = "<ul>"
                for attr in attrs:
                    summary += f"<li><strong>{attr.attribute_value.attribute.name}:</strong> {attr.attribute_value.value}"
                    if attr.attribute_value.hex_color:
                        summary += f' <div style="width: 15px; height: 15px; background-color: {attr.attribute_value.hex_color}; border: 1px solid #ccc; display: inline-block; margin-left: 5px;"></div>'
                    summary += "</li>"
                summary += "</ul>"
                return mark_safe(summary)
            return "No attributes assigned"
        return "Save first to add attributes"
    attributes_summary.short_description = "Attributes Summary"


@admin.register(ProductVariantAttribute)
class ProductVariantAttributeAdmin(admin.ModelAdmin):
    list_display = ('variant', 'attribute_name',
                    'attribute_value', 'hex_color_display')
    list_filter = ('attribute_value__attribute',)
    search_fields = ('variant__sku', 'variant__name', 'attribute_value__value')
    autocomplete_fields = ['variant', 'attribute_value']

    def attribute_name(self, obj):
        return obj.attribute_value.attribute.name
    attribute_name.short_description = "Attribute"

    def hex_color_display(self, obj):
        if obj.attribute_value.hex_color:
            return format_html(
                '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; display: inline-block;"></div>',
                obj.attribute_value.hex_color
            )
        return "-"
    hex_color_display.short_description = "Color"


# Customize admin site
admin.site.site_header = "Ecommerce Product Management"
admin.site.site_title = "Product Admin"
admin.site.index_title = "Welcome to Product Management System"
