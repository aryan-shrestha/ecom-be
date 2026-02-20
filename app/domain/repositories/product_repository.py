"""Product repository interface."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.product import Product, ProductStatus
from app.domain.entities.product_variant import ProductVariant
from app.domain.entities.product_image import ProductImage
from app.domain.entities.variant_image import VariantImage
from app.domain.value_objects.slug import Slug


class ProductRepository(ABC):
    """Repository interface for Product aggregate."""

    @abstractmethod
    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """Retrieve product by ID."""
        ...

    @abstractmethod
    async def get_by_slug(self, slug: Slug) -> Optional[Product]:
        """Retrieve product by slug."""
        ...

    @abstractmethod
    async def exists_by_slug(self, slug: Slug) -> bool:
        """Check if product exists with given slug."""
        ...

    @abstractmethod
    async def save(self, product: Product) -> Product:
        """Save new product."""
        ...

    @abstractmethod
    async def update(self, product: Product) -> Product:
        """Update existing product."""
        ...

    @abstractmethod
    async def delete(self, product_id: UUID) -> None:
        """Delete product (soft delete recommended)."""
        ...

    @abstractmethod
    async def list_paginated(
        self,
        offset: int,
        limit: int,
        status: Optional[ProductStatus] = None,
        category_id: Optional[UUID] = None,
        tag: Optional[str] = None,
        featured: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> tuple[list[Product], int]:
        """
        List products with pagination and filters.
        
        Returns:
            Tuple of (products, total_count)
        """
        ...

    # Variant operations

    @abstractmethod
    async def get_variant_by_id(self, variant_id: UUID) -> Optional[ProductVariant]:
        """Retrieve variant by ID."""
        ...

    @abstractmethod
    async def get_variant_by_sku(self, sku: str) -> Optional[ProductVariant]:
        """Retrieve variant by SKU."""
        ...

    @abstractmethod
    async def get_variants_for_product(self, product_id: UUID) -> list[ProductVariant]:
        """Get all variants for a product."""
        ...

    @abstractmethod
    async def save_variant(self, variant: ProductVariant) -> ProductVariant:
        """Save new variant."""
        ...

    @abstractmethod
    async def update_variant(self, variant: ProductVariant) -> ProductVariant:
        """Update existing variant."""
        ...

    @abstractmethod
    async def delete_variant(self, variant_id: UUID) -> None:
        """Delete variant."""
        ...

    # Image operations

    @abstractmethod
    async def get_image_by_id(self, image_id: UUID) -> Optional[ProductImage]:
        """Retrieve image by ID."""
        ...

    @abstractmethod
    async def get_images_for_product(self, product_id: UUID) -> list[ProductImage]:
        """Get all images for a product, ordered by position."""
        ...

    @abstractmethod
    async def save_image(self, image: ProductImage) -> ProductImage:
        """Save new image."""
        ...

    @abstractmethod
    async def update_image(self, image: ProductImage) -> ProductImage:
        """Update existing image."""
        ...

    @abstractmethod
    async def delete_image(self, image_id: UUID) -> None:
        """Delete image."""
        ...

    @abstractmethod
    async def reorder_images(self, product_id: UUID, image_positions: dict[UUID, int]) -> None:
        """
        Reorder product images.
        
        Args:
            product_id: Product ID
            image_positions: Map of image_id -> new_position
        """
        ...

    # Category assignments

    @abstractmethod
    async def get_category_ids_for_product(self, product_id: UUID) -> list[UUID]:
        """Get category IDs assigned to product."""
        ...

    @abstractmethod
    async def assign_categories(self, product_id: UUID, category_ids: list[UUID]) -> None:
        """Assign categories to product (replaces existing)."""
        ...

    # Variant image operations

    @abstractmethod
    async def get_variant_image_by_id(self, image_id: UUID) -> Optional[VariantImage]:
        """Retrieve variant image by ID."""
        ...

    @abstractmethod
    async def get_images_for_variant(self, variant_id: UUID) -> list[VariantImage]:
        """Get all images for a variant, ordered by position."""
        ...

    @abstractmethod
    async def save_variant_image(self, image: VariantImage) -> VariantImage:
        """Save new variant image."""
        ...

    @abstractmethod
    async def update_variant_image(self, image: VariantImage) -> VariantImage:
        """Update existing variant image."""
        ...

    @abstractmethod
    async def delete_variant_image(self, image_id: UUID) -> None:
        """Delete variant image."""
        ...
