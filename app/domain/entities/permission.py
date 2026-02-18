"""Permission domain entity."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Permission:
    """Permission domain entity representing a specific permission code."""

    id: UUID
    code: str

    def __post_init__(self) -> None:
        """Validate permission code."""
        if not self.code or not self.code.strip():
            raise ValueError("Permission code cannot be empty")
        if len(self.code) > 100:
            raise ValueError("Permission code cannot exceed 100 characters")
        # Permission codes should follow pattern like "resource:action"
        if ":" not in self.code:
            raise ValueError("Permission code must follow 'resource:action' pattern")
