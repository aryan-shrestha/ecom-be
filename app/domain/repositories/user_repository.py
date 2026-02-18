"""User repository interface - lives in domain, implemented in infrastructure."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.user import User
from app.domain.value_objects.email import Email


class UserRepository(ABC):
    """Repository interface for User aggregate."""

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Retrieve user by ID."""
        ...

    @abstractmethod
    async def get_by_email(self, email: Email) -> Optional[User]:
        """Retrieve user by email."""
        ...

    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool:
        """Check if user exists with given email."""
        ...

    @abstractmethod
    async def save(self, user: User) -> User:
        """Save new user (insert)."""
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update existing user."""
        ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        """Delete user by ID."""
        ...
