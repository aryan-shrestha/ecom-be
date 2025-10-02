from django.db import models
from django.utils import timezone

from product.models import Product, ProductVariant


class DiscountRule(models.Model):
    """Discount management system"""
    DISCOUNT_TYPES = [
        ('PERCENTAGE', 'Percentage'),
        ('FIXED', 'Fixed Amount'),
        ('BOGO', 'Buy One Get One'),
    ]

    APPLY_TO = [
        ('PRODUCT', 'Specific Product'),
        ('CATEGORY', 'Category'),
        ('ALL', 'All Products'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    apply_to = models.CharField(max_length=20, choices=APPLY_TO)

    # Conditions
    minimum_quantity = models.PositiveIntegerField(default=1)
    minimum_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    maximum_uses = models.PositiveIntegerField(null=True, blank=True)
    current_uses = models.PositiveIntegerField(default=0)

    # Validity
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def is_valid(self):
        """Check if discount is currently valid"""
        now = timezone.now()
        return (self.is_active and
                self.start_date <= now <= self.end_date and
                (self.maximum_uses is None or self.current_uses < self.maximum_uses))

    class Meta:
        verbose_name = 'Discount Rule'
        verbose_name_plural = 'Discount Rules'


class ProductDiscount(models.Model):
    """Link specific products to discount rules"""
    discount_rule = models.ForeignKey(
        DiscountRule, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='discounts')

    class Meta:
        unique_together = ('discount_rule', 'product')
        verbose_name = 'Product Discount'
        verbose_name_plural = 'Product Discounts'

    def __str__(self):
        return f"{self.product.name} - {self.discount_rule.name}"


class BulkPricingTier(models.Model):
    """Bulk pricing for B2B customers"""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='bulk_pricing')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE,
                                null=True, blank=True, related_name='bulk_pricing')

    min_quantity = models.PositiveIntegerField()
    max_quantity = models.PositiveIntegerField(null=True, blank=True)

    # Pricing options
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    fixed_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'variant', 'min_quantity')
        ordering = ['min_quantity']
        verbose_name = 'Bulk Pricing Tier'
        verbose_name_plural = 'Bulk Pricing Tiers'

    def get_price(self, base_price):
        """Calculate bulk price based on base price"""
        if self.fixed_price:
            return float(self.fixed_price)
        elif self.discount_percentage:
            discount = float(base_price) * \
                (float(self.discount_percentage) / 100)
            return float(base_price) - discount
        return float(base_price)

    def __str__(self):
        variant_info = f" - {self.variant.name}" if self.variant else ""
        return f"{self.product.name}{variant_info} - {self.min_quantity}+ units"
