"""
Product size repository interface
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.size import Size


class SizeRepository(ABC):
    
    """Repository interface for Size entity."""

    @abstractmethod
    async def get_by_id(self, size_id: UUID) -> Optional[Size]:
        """Retrieve size by ID."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Size]:
        """List all sizes."""
        ...

    @abstractmethod
    async def list_by_product_id(self, product_id: UUID) -> list[Size]:
        """List all sizes for a given product ID."""
        ...

    @abstractmethod
    async def save(self, size: Size) -> Size:
        """Save new size."""
        ...

    @abstractmethod
    async def update(self, size: Size) -> Size:
        """Update existing size."""
        ...

    @abstractmethod
    async def delete(self, size_id: UUID) -> None:
        """Delete size (soft delete recommended)."""
        ...