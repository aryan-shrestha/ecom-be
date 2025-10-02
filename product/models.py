
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
import uuid

from category.models import Category
from utils.validators import validate_array_of_urls, validate_no_special_symbols

# Create your models here.


class Product(models.Model):
    name = models.CharField(max_length=255, unique=False, null=False, validators=[
                            validate_no_special_symbols])
    slug = models.CharField(max_length=255, unique=True, null=False, validators=[
                            validate_no_special_symbols])
    description = models.TextField(unique=False, null=False)
    category = models.ForeignKey(
        Category, null=False, on_delete=models.CASCADE, related_name="products")
    price = models.FloatField(null=False)
    images = models.JSONField(null=True, blank=True, validators=[
                              validate_array_of_urls])
    created_at = models.DateField(auto_now_add=True)
    modified_at = models.DateField(auto_now=True)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        # Generate slug if not set or if name has changed
        if not self.slug or slugify(self.name) != self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            if Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                unique_suffix = uuid.uuid4().hex[:8]
                slug = f"{base_slug}-{unique_suffix}"
            self.slug = slug

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'


# Product Variants & Options Models

class ProductAttribute(models.Model):
    """Define attributes like Color, Size, Material, etc."""
    name = models.CharField(
        max_length=100, unique=True)  # e.g., "Color", "Size"
    display_name = models.CharField(max_length=100)  # e.g., "Choose Color"
    is_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Product Attribute'
        verbose_name_plural = 'Product Attributes'


class ProductAttributeValue(models.Model):
    """Define specific values for attributes like Red, Blue for Color"""
    attribute = models.ForeignKey(
        ProductAttribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=100)  # e.g., "Red", "Large", "Cotton"
    display_value = models.CharField(
        max_length=100, blank=True)  # For display purposes
    hex_color = models.CharField(
        max_length=7, blank=True, null=True)  # For color attributes

    class Meta:
        unique_together = ('attribute', 'value')
        verbose_name = 'Product Attribute Value'
        verbose_name_plural = 'Product Attribute Values'

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductVariant(models.Model):
    """Individual product variants with specific attribute combinations"""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=100, unique=True)
    # e.g., "Red Large T-Shirt"
    name = models.CharField(max_length=255, blank=True)
    price_adjustment = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    images = models.JSONField(null=True, blank=True, validators=[
                              validate_array_of_urls])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.name or self.sku}"

    @property
    def final_price(self):
        """Calculate final price including adjustments"""
        return float(self.product.price) + float(self.price_adjustment)

    class Meta:
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'


class ProductVariantAttribute(models.Model):
    """Link variants to their specific attribute values"""
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name='attributes')
    attribute_value = models.ForeignKey(
        ProductAttributeValue, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('variant', 'attribute_value')
        verbose_name = 'Product Variant Attribute'
        verbose_name_plural = 'Product Variant Attributes'

    def __str__(self):
        return f"{self.variant} - {self.attribute_value}"
