"""Product domain entity."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from app.domain.value_objects.slug import Slug


class ProductStatus(Enum):
    """Product publication status."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True)
class Product:
    """Product aggregate root."""

    id: UUID
    status: ProductStatus
    name: str
    slug: Slug
    description_short: Optional[str]
    description_long: Optional[str]
    tags: list[str]
    featured: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    def __post_init__(self) -> None:
        """Validate product invariants."""
        if not self.name or not self.name.strip():
            raise ValueError("Product name cannot be empty")
        if len(self.name) > 255:
            raise ValueError("Product name cannot exceed 255 characters")
        if self.description_short and len(self.description_short) > 500:
            raise ValueError("Short description cannot exceed 500 characters")
        if self.sort_order < 0:
            raise ValueError("Sort order cannot be negative")
        # Validate tags are strings
        if not all(isinstance(tag, str) for tag in self.tags):
            raise ValueError("All tags must be strings")

    def is_published(self) -> bool:
        """Check if product is published."""
        return self.status == ProductStatus.PUBLISHED

    def is_draft(self) -> bool:
        """Check if product is draft."""
        return self.status == ProductStatus.DRAFT

    def is_archived(self) -> bool:
        """Check if product is archived."""
        return self.status == ProductStatus.ARCHIVED

    def with_status(self, status: ProductStatus, updated_at: datetime, updated_by: Optional[UUID] = None) -> "Product":
        """Return new Product with updated status."""
        return Product(
            id=self.id,
            status=status,
            name=self.name,
            slug=self.slug,
            description_short=self.description_short,
            description_long=self.description_long,
            tags=self.tags,
            featured=self.featured,
            sort_order=self.sort_order,
            created_at=self.created_at,
            updated_at=updated_at,
            created_by=self.created_by,
            updated_by=updated_by,
        )

    def publish(self, updated_at: datetime, updated_by: Optional[UUID] = None) -> "Product":
        """Publish product (status transition validated by policy)."""
        return self.with_status(ProductStatus.PUBLISHED, updated_at, updated_by)

    def archive(self, updated_at: datetime, updated_by: Optional[UUID] = None) -> "Product":
        """Archive product."""
        return self.with_status(ProductStatus.ARCHIVED, updated_at, updated_by)

    def update_details(
        self,
        name: str,
        description_short: Optional[str],
        description_long: Optional[str],
        tags: list[str],
        featured: bool,
        sort_order: int,
        updated_at: datetime,
        updated_by: Optional[UUID] = None,
    ) -> "Product":
        """Return new Product with updated details."""
        return Product(
            id=self.id,
            status=self.status,
            name=name,
            slug=self.slug,  # Slug not changed in update
            description_short=description_short,
            description_long=description_long,
            tags=tags,
            featured=featured,
            sort_order=sort_order,
            created_at=self.created_at,
            updated_at=updated_at,
            created_by=self.created_by,
            updated_by=updated_by,
        )
