"""
Product variant image repository interface.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.variant_image import VariantImage

class ProductVariantImageRepository(ABC):
    
    """Repository interface for VariantImage entity."""

    @abstractmethod
    async def get_by_id(self, image_id: UUID) -> Optional[VariantImage]:
        """Retrieve variant image by ID."""
        ...

    @abstractmethod
    async def list_by_variant_id(self, variant_id: UUID) -> list[VariantImage]:
        """List all images for a given product variant ID."""
        ...

    @abstractmethod
    async def save(self, image: VariantImage) -> VariantImage:
        """Save new variant image."""
        ...

    @abstractmethod
    async def update(self, image: VariantImage) -> VariantImage:
        """Update existing variant image."""
        ...

    @abstractmethod
    async def delete(self, image_id: UUID) -> None:
        """Delete variant image (soft delete recommended)."""
        ...