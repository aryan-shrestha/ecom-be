"""Refresh token repository interface."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.refresh_token import RefreshToken


class RefreshTokenRepository(ABC):
    """Repository interface for RefreshToken aggregate."""

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Retrieve refresh token by its hash."""
        ...

    @abstractmethod
    async def save(self, refresh_token: RefreshToken) -> RefreshToken:
        """Save new refresh token."""
        ...

    @abstractmethod
    async def update(self, refresh_token: RefreshToken) -> RefreshToken:
        """Update existing refresh token."""
        ...

    @abstractmethod
    async def revoke_by_token_hash(self, token_hash: str, revoked_at) -> None:
        """Revoke refresh token by hash."""
        ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: UUID, revoked_at) -> None:
        """Revoke all refresh tokens for a user."""
        ...

    @abstractmethod
    async def revoke_family(self, family_id: UUID, revoked_at) -> None:
        """Revoke all refresh tokens in a family (for reuse detection)."""
        ...

    @abstractmethod
    async def delete_expired(self, before) -> int:
        """Delete expired tokens (cleanup). Returns number deleted."""
        ...
