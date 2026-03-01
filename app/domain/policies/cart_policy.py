"""Cart domain policy."""

from app.domain.entities.cart import Cart, CartItem
from app.domain.entities.product import Product, ProductStatus
from app.domain.entities.product_variant import ProductVariant, VariantStatus
from app.domain.errors.domain_errors import (
    CartAlreadyConvertedError,
    CartItemQuantityError,
    VariantNotAvailableError,
)

MAX_QUANTITY_PER_ITEM = 100


class CartPolicy:
    """Domain policy for cart operations."""

    @staticmethod
    def validate_cart_is_active(cart: Cart) -> None:
        """Ensure the cart can still be modified."""
        if not cart.is_active():
            raise CartAlreadyConvertedError(
                f"Cart {cart.id} is not active (status: {cart.status.value})"
            )

    @staticmethod
    def validate_variant_available(
        product: Product, variant: ProductVariant
    ) -> None:
        """
        Validate that the variant is purchasable on the storefront.

        - Product must be PUBLISHED (not ARCHIVED / DRAFT)
        - Variant must be ACTIVE
        """
        if product.status != ProductStatus.PUBLISHED:
            raise VariantNotAvailableError(
                f"Product '{product.name}' is not published (status: {product.status.value})"
            )
        if variant.status != VariantStatus.ACTIVE:
            raise VariantNotAvailableError(
                f"Variant {variant.id} is not active (status: {variant.status.value})"
            )

    @staticmethod
    def validate_quantity(quantity: int) -> None:
        """Validate item quantity."""
        if quantity < 1:
            raise CartItemQuantityError("Quantity must be at least 1")
        if quantity > MAX_QUANTITY_PER_ITEM:
            raise CartItemQuantityError(
                f"Quantity cannot exceed {MAX_QUANTITY_PER_ITEM} per item"
            )
