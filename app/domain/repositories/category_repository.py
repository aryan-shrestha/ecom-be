"""Category repository interface."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.category import Category
from app.domain.value_objects.slug import Slug


class CategoryRepository(ABC):
    """Repository interface for Category entity."""

    @abstractmethod
    async def get_by_id(self, category_id: UUID) -> Optional[Category]:
        """Retrieve category by ID."""
        ...

    @abstractmethod
    async def get_by_slug(self, slug: Slug) -> Optional[Category]:
        """Retrieve category by slug."""
        ...

    @abstractmethod
    async def exists_by_slug(self, slug: Slug) -> bool:
        """Check if category exists with given slug."""
        ...

    @abstractmethod
    async def get_children(self, parent_id: UUID) -> list[Category]:
        """Get child categories."""
        ...

    @abstractmethod
    async def get_root_categories(self) -> list[Category]:
        """Get root categories (no parent)."""
        ...

    @abstractmethod
    async def save(self, category: Category) -> Category:
        """Save new category."""
        ...

    @abstractmethod
    async def update(self, category: Category) -> Category:
        """Update existing category."""
        ...

    @abstractmethod
    async def delete(self, category_id: UUID) -> None:
        """Delete category."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Category]:
        """List all categories."""
        ...
