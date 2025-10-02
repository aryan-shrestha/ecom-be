from django.dispatch import receiver
from django.db.models.signals import post_delete

from cart.models import Cart, CartItem


@receiver(post_delete, sender=CartItem)
def update_cart_total_after_delete(sender, instance: CartItem, **kwargs: dict[str, any]):
    if instance.cart:
        instance.cart.update_total()
