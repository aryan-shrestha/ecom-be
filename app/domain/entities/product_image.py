"""Product image domain entity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class ProductImage:
    """Product image entity."""

    id: UUID
    product_id: UUID
    url: str
    alt_text: Optional[str]
    position: int
    created_at: datetime

    def __post_init__(self) -> None:
        """Validate image invariants."""
        if not self.url or not self.url.strip():
            raise ValueError("Image URL cannot be empty")
        if len(self.url) > 1000:
            raise ValueError("Image URL cannot exceed 1000 characters")
        if self.alt_text and len(self.alt_text) > 255:
            raise ValueError("Alt text cannot exceed 255 characters")
        if self.position < 0:
            raise ValueError("Image position cannot be negative")

    def update_position(self, position: int) -> "ProductImage":
        """Return new image with updated position."""
        return ProductImage(
            id=self.id,
            product_id=self.product_id,
            url=self.url,
            alt_text=self.alt_text,
            position=position,
            created_at=self.created_at,
        )
