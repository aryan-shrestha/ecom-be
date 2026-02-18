"""Refresh token domain entity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class RefreshToken:
    """
    Refresh token domain entity.
    
    Supports token rotation and reuse detection via family tracking.
    """

    id: UUID
    user_id: UUID
    token_hash: str
    family_id: UUID
    issued_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime]
    replaced_by_token_id: Optional[UUID]
    ip: Optional[str] = None
    user_agent: Optional[str] = None

    def is_expired(self, current_time: datetime) -> bool:
        """Check if token is expired."""
        return current_time >= self.expires_at

    def is_revoked(self) -> bool:
        """Check if token has been revoked."""
        return self.revoked_at is not None

    def is_replaced(self) -> bool:
        """Check if token has been replaced (indicates potential reuse)."""
        return self.replaced_by_token_id is not None

    def can_be_used(self, current_time: datetime) -> bool:
        """Check if token can be used for refresh."""
        return (
            not self.is_expired(current_time)
            and not self.is_revoked()
            and not self.is_replaced()
        )

    def revoke(self, revoked_at: datetime) -> "RefreshToken":
        """Return new RefreshToken instance marked as revoked."""
        return RefreshToken(
            id=self.id,
            user_id=self.user_id,
            token_hash=self.token_hash,
            family_id=self.family_id,
            issued_at=self.issued_at,
            expires_at=self.expires_at,
            revoked_at=revoked_at,
            replaced_by_token_id=self.replaced_by_token_id,
            ip=self.ip,
            user_agent=self.user_agent,
        )

    def mark_as_replaced(self, replaced_by_id: UUID) -> "RefreshToken":
        """Return new RefreshToken instance marked as replaced."""
        return RefreshToken(
            id=self.id,
            user_id=self.user_id,
            token_hash=self.token_hash,
            family_id=self.family_id,
            issued_at=self.issued_at,
            expires_at=self.expires_at,
            revoked_at=self.revoked_at,
            replaced_by_token_id=replaced_by_id,
            ip=self.ip,
            user_agent=self.user_agent,
        )
