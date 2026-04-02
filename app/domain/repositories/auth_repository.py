"""Authentication repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.role import Role


class AuthRepository(ABC):
    """Repository interface for authentication operations."""

    @abstractmethod
    async def get_user_roles(self, user_id: UUID) -> list[Role]:
        """Get list of roles assigned to user."""
        ...

    @abstractmethod
    async def assign_role_to_user(self, user_id: UUID, role_name: str) -> None:
        """Assign role to user."""
        ...

    @abstractmethod
    async def remove_role_from_user(self, user_id: UUID, role_name: str) -> None:
        """Remove role from user."""
        ...
