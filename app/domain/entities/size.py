""" Size domain entity. """
from dataclasses import dataclass
import datetime
from uuid import UUID

@dataclass(frozen=True)
class Size:
    """Size domain entity representing a product size."""

    id: UUID
    name: str
    product_id: UUID
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Validate size name."""
        if not self.name or not self.name.strip():
            raise ValueError("Size name cannot be empty")
        if len(self.name) > 50:
            raise ValueError("Size name cannot exceed 50 characters")