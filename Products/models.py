from django.db import models
from cloudinary.models import CloudinaryField
from category.models import Category

# Create your models here.


def calculate_discount_percentage(original_price, discounted_price):
    if original_price <= 0 or discounted_price < 0:
        raise ValueError(
            "Original price must be greater than 0, and discounted price must not be negative.")

    discount_amount = original_price - discounted_price
    discount_percentage = (discount_amount / original_price) * 100

    return discount_percentage


class Product(models.Model):
    name = models.CharField(max_length=255, unique=False, null=False)
    slug = models.CharField(max_length=255, unique=True, null=False)
    description = models.TextField(unique=False, null=False)
    category = models.ForeignKey(
        Category, null=False, on_delete=models.CASCADE, related_name="products")
    og_price = models.FloatField(null=False)
    dis_price = models.FloatField(null=True, blank=True)
    stock = models.IntegerField(null=False, default=0)
    dis_percentage = models.DecimalField(
        max_digits=10, decimal_places=0, null=True, editable=False)
    created_at = models.DateField(auto_now_add=True)
    modified_at = models.DateField(auto_now=True)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        self.dis_percentage = calculate_discount_percentage(
            original_price=self.og_price, discounted_price=self.dis_price)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'


class ProductImages(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=False, related_name='images')
    image = CloudinaryField('image')

    def __str__(self):
        return self.product.name

    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
