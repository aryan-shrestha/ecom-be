"""Role domain entity."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Role:
    """Role domain entity representing a named role in the RBAC system."""

    id: UUID
    name: str

    def __post_init__(self) -> None:
        """Validate role name."""
        if not self.name or not self.name.strip():
            raise ValueError("Role name cannot be empty")
        if len(self.name) > 50:
            raise ValueError("Role name cannot exceed 50 characters")
