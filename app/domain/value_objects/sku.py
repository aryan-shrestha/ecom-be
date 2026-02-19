"""SKU value object."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SKU:
    """Stock Keeping Unit value object."""

    value: str

    def __post_init__(self) -> None:
        """Validate SKU format."""
        if not self.value or not self.value.strip():
            raise ValueError("SKU cannot be empty")
        if len(self.value) > 100:
            raise ValueError("SKU cannot exceed 100 characters")
        # SKU should be alphanumeric with hyphens/underscores
        if not re.match(r"^[A-Z0-9_-]+$", self.value):
            raise ValueError(
                "SKU must contain only uppercase alphanumeric characters, "
                "hyphens, and underscores"
            )

    @classmethod
    def from_string(cls, value: str) -> "SKU":
        """Create SKU from string (normalizes to uppercase)."""
        normalized = value.upper().strip()
        return cls(value=normalized)

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __repr__(self) -> str:
        """Debug representation."""
        return f"SKU('{self.value}')"
