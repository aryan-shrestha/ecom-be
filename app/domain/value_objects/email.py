"""Email value object with domain-level validation."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """Email value object ensuring valid email format."""

    value: str

    def __post_init__(self) -> None:
        """Validate email format."""
        if not self.value or not self.value.strip():
            raise ValueError("Email cannot be empty")
        
        # Basic email validation (domain-level, not comprehensive)
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, self.value):
            raise ValueError("Invalid email format")
        
        if len(self.value) > 255:
            raise ValueError("Email cannot exceed 255 characters")

    def __str__(self) -> str:
        """Return string representation."""
        return self.value

    def normalize(self) -> "Email":
        """Return normalized email (lowercase)."""
        return Email(self.value.lower())
