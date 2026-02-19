"""Slug value object."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Slug:
    """Slug value object for URL-friendly identifiers."""

    value: str

    def __post_init__(self) -> None:
        """Validate slug format."""
        if not self.value or not self.value.strip():
            raise ValueError("Slug cannot be empty")
        if len(self.value) > 200:
            raise ValueError("Slug cannot exceed 200 characters")
        # Slug must be lowercase alphanumeric with hyphens
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", self.value):
            raise ValueError(
                "Slug must be lowercase alphanumeric with hyphens, "
                "no leading/trailing hyphens or consecutive hyphens"
            )

    @classmethod
    def from_string(cls, text: str) -> "Slug":
        """
        Create slug from arbitrary string.
        
        Converts to lowercase, replaces spaces with hyphens, removes invalid chars.
        """
        # Convert to lowercase and replace spaces with hyphens
        slug = text.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)  # Remove invalid chars
        slug = re.sub(r"[-\s]+", "-", slug)  # Replace spaces/hyphens with single hyphen
        slug = slug.strip("-")  # Remove leading/trailing hyphens

        if not slug:
            raise ValueError("Cannot generate valid slug from provided text")

        return cls(value=slug)

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __repr__(self) -> str:
        """Debug representation."""
        return f"Slug('{self.value}')"
