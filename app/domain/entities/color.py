"""Color domain entity."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)
class Color:
    """Color domain entity representing a product color."""

    id: UUID
    name: str
    hex_value: str
    product_id: UUID
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Validate color name."""
        if not self.name or not self.name.strip():
            raise ValueError("Color name cannot be empty")
        if len(self.name) > 50:
            raise ValueError("Color name cannot exceed 50 characters")
        if not self.hex_value or not self.hex_value.strip():
            raise ValueError("Color hex value cannot be empty")
        if len(self.hex_value) != 7 or not self.hex_value.startswith("#"):
            raise ValueError("Color hex value must be a valid hex color code (e.g., #FF0000)")