"""Category domain entity."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.domain.value_objects.slug import Slug


@dataclass(frozen=True)
class Category:
    """Category entity for product categorization."""

    id: UUID
    name: str
    slug: Slug
    parent_id: Optional[UUID]

    def __post_init__(self) -> None:
        """Validate category invariants."""
        if not self.name or not self.name.strip():
            raise ValueError("Category name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Category name cannot exceed 100 characters")
        # Cannot be its own parent
        if self.parent_id == self.id:
            raise ValueError("Category cannot be its own parent")

    def is_root(self) -> bool:
        """Check if category is a root category."""
        return self.parent_id is None

    def update(self, name: str, parent_id: Optional[UUID]) -> "Category":
        """Return new category with updated details."""
        return Category(
            id=self.id,
            name=name,
            slug=self.slug,  # Slug not changed in update
            parent_id=parent_id,
        )
