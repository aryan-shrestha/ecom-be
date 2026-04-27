"""
Product variant repository interface
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.product_variant import ProductVariant

class ProductVariantRepository(ABC):
    
    """Repository interface for ProductVariant entity."""

    @abstractmethod
    async def get_by_id(self, variant_id: UUID) -> Optional[ProductVariant]:
        """Retrieve product variant by ID."""
        ...

    @abstractmethod
    async def get_by_color_and_size(self, product_id: UUID, color_id: UUID, size_id: UUID) -> Optional[ProductVariant]:
        """Retrieve product variant by product ID, color ID, and size ID."""
        ...
    
    @abstractmethod
    async def list_by_product_id(self, product_id: UUID) -> list[ProductVariant]:
        """List all variants for a given product ID."""
        ...

    @abstractmethod
    async def save(self, variant: ProductVariant) -> ProductVariant:
        """Save new product variant."""
        ...

    @abstractmethod
    async def update(self, variant: ProductVariant) -> ProductVariant:
        """Update existing product variant."""
        ...

    @abstractmethod
    async def delete(self, variant_id: UUID) -> None:
        """Delete product variant (soft delete recommended)."""
        ...
    