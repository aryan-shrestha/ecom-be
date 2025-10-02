from django.db import models
from django.db.models import F, Sum, Case, When
from django.contrib.auth.models import User

from product.models import Product

# Create your models here.


class Cart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    date_added = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        # Ensure unique constraints
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(user__isnull=False),
                name='unique_user_cart'
            ),
        ]

    def update_total(self):
        # Calculate the total price of all items in the cart, considering discounts
        total = self.items.aggregate(
            total_price=Sum(
                F('quantity') * Case(
                    When(product__dis_price__lt=F('product__og_price'),
                         then=F('product__dis_price')),
                    default=F('product__og_price'),
                    output_field=models.FloatField(),
                )
            )
        )['total_price']

        self.total = total if total is not None else 0
        self.save()

    def __str__(self):
        if self.user:
            return f"#CRT-{self.id}"


class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, null=True, related_name='items')
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
