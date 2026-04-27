"""
Color repository interface
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.color import Color

class ColorRepository(ABC):
    """Repository interface for color entity"""

    @abstractmethod
    async def get_by_id(self, color_id: UUID) -> Optional[Color]:
        """Retrieve color by ID."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Color]:
        """List all colors."""
        ...

    @abstractmethod
    async def list_by_product_id(self, product_id: UUID) -> list[Color]:
        """List all colors for a given product ID."""
        ...

    @abstractmethod
    async def save(self, color: Color) -> Color:
        """Save new color."""
        ...

    @abstractmethod
    async def update(self, color: Color) -> Color:
        """Update existing color."""
        ...

    @abstractmethod
    async def delete(self, color_id: UUID) -> None:
        """Delete color (soft delete recommended)."""
        ...