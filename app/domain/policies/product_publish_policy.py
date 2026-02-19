"""Product publish policy."""

from typing import Optional

from app.domain.entities.product import Product, ProductStatus
from app.domain.entities.product_variant import VariantStatus
from app.domain.errors.domain_errors import ProductPublishError


class ProductPublishPolicy:
    """
    Domain policy for product publishing rules.
    
    A product can only be published if:
    1. Product has name and slug
    2. Product has at least one ACTIVE variant
    3. All ACTIVE variants have valid price and SKU
    """

    @staticmethod
    def can_publish(
        product: Product,
        variants: list[tuple[object, VariantStatus, bool]],  # (variant, status, has_price_and_sku)
    ) -> tuple[bool, Optional[str]]:
        """
        Check if product can be published.
        
        Args:
            product: Product to publish
            variants: List of (variant, status, has_valid_pricing) tuples
            
        Returns:
            Tuple of (can_publish, reason_if_not)
        """
        # Product must not be archived
        if product.is_archived():
            return False, "Cannot publish archived product"

        # Product must have name and slug
        if not product.name or not product.name.strip():
            return False, "Product must have a name"

        # Must have at least one active variant
        active_variants = [v for v in variants if v[1] == VariantStatus.ACTIVE]
        if not active_variants:
            return False, "Product must have at least one active variant"

        # All active variants must have valid price and SKU
        for variant, status, has_valid_pricing in active_variants:
            if not has_valid_pricing:
                return False, "All active variants must have valid price and SKU"

        return True, None

    @staticmethod
    def ensure_can_publish(
        product: Product,
        variants: list[tuple[object, VariantStatus, bool]],
    ) -> None:
        """
        Ensure product can be published, raise error if not.
        
        Raises:
            ProductPublishError: If product cannot be published
        """
        can_publish, reason = ProductPublishPolicy.can_publish(product, variants)
        if not can_publish:
            raise ProductPublishError(f"Cannot publish product: {reason}")
