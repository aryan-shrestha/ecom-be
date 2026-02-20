"""Variant image domain entity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class VariantImage:
    """Variant image entity."""

    id: UUID
    variant_id: UUID
    url: str
    alt_text: Optional[str]
    position: int
    created_at: datetime
    provider: Optional[str] = None
    provider_public_id: Optional[str] = None
    bytes_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None

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
        if self.provider and len(self.provider) > 50:
            raise ValueError("Provider name cannot exceed 50 characters")
        if self.provider_public_id and len(self.provider_public_id) > 500:
            raise ValueError("Provider public ID cannot exceed 500 characters")
        if self.bytes_size is not None and self.bytes_size < 0:
            raise ValueError("Bytes size cannot be negative")
        if self.width is not None and self.width < 0:
            raise ValueError("Width cannot be negative")
        if self.height is not None and self.height < 0:
            raise ValueError("Height cannot be negative")
        if self.format and len(self.format) > 20:
            raise ValueError("Format cannot exceed 20 characters")

    def update_position(self, position: int) -> "VariantImage":
        """Return new image with updated position."""
        return VariantImage(
            id=self.id,
            variant_id=self.variant_id,
            url=self.url,
            alt_text=self.alt_text,
            position=position,
            created_at=self.created_at,
            provider=self.provider,
            provider_public_id=self.provider_public_id,
            bytes_size=self.bytes_size,
            width=self.width,
            height=self.height,
            format=self.format,
        )
