from django.db import models
from django.db.models import F, Sum, Case, When
from django.db.models.signals import post_delete
from django.dispatch import receiver

from Products.models import Product

# Create your models here.

class Cart(models.Model):
    session_key = models.CharField(max_length=32, unique=True)
    date_added = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    
    def update_total(self):
        # Calculate the total price of all items in the cart, considering discounts
        total = self.items.aggregate(
            total_price=Sum(
                F('quantity') * Case(
                    When(product__dis_price__lt=F('product__og_price'), then=F('product__dis_price')),
                    default=F('product__og_price'),
                    output_field=models.FloatField(),
                )
            )
        )['total_price']

        self.total = total if total is not None else 0
        self.save()

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True, related_name='items')
    quantity = models.IntegerField(null=True, default=0)
    is_checked_out = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # check if the CartItem instance already exits in the database
        if self.pk is None and self.cart_id is not None:
            super().save(*args, **kwargs)
        
        else:
            # this is an existing CartItem instance, update and save
            super().save(*args, *kwargs)

            # update the cart total when a cart item is updated
            if self.cart:
                self.cart.update_total()

@receiver(post_delete, sender=CartItem)
def update_cart_total_after_delete(sender, instance, **kwargs):
    if instance.cart:
        instance.cart.update_total()