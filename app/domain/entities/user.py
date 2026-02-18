"""Domain layer entities - pure Python with no external dependencies."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.domain.value_objects.email import Email


@dataclass(frozen=True)
class User:
    """User domain entity representing an authenticated user in the system."""

    id: UUID
    email: Email
    password_hash: str
    is_active: bool
    is_verified: bool
    token_version: int
    created_at: datetime
    updated_at: datetime

    def with_new_password(self, password_hash: str, updated_at: datetime) -> "User":
        """Return new User instance with updated password and incremented token_version."""
        return User(
            id=self.id,
            email=self.email,
            password_hash=password_hash,
            is_active=self.is_active,
            is_verified=self.is_verified,
            token_version=self.token_version + 1,
            created_at=self.created_at,
            updated_at=updated_at,
        )

    def with_token_version_incremented(self, updated_at: datetime) -> "User":
        """Return new User instance with incremented token_version (for session revocation)."""
        return User(
            id=self.id,
            email=self.email,
            password_hash=self.password_hash,
            is_active=self.is_active,
            is_verified=self.is_verified,
            token_version=self.token_version + 1,
            created_at=self.created_at,
            updated_at=updated_at,
        )

    def deactivate(self, updated_at: datetime) -> "User":
        """Return new User instance marked as inactive."""
        return User(
            id=self.id,
            email=self.email,
            password_hash=self.password_hash,
            is_active=False,
            is_verified=self.is_verified,
            token_version=self.token_version + 1,
            created_at=self.created_at,
            updated_at=updated_at,
        )
