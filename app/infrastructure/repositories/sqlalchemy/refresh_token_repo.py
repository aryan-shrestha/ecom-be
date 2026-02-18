"""SQLAlchemy implementation of RefreshTokenRepository."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.refresh_token import RefreshToken
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository
from app.infrastructure.db.sqlalchemy.models.refresh_token_model import RefreshTokenModel
from app.infrastructure.mappers.refresh_token_mapper import RefreshTokenMapper


class SqlAlchemyRefreshTokenRepository(RefreshTokenRepository):
    """SQLAlchemy implementation of RefreshTokenRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Retrieve refresh token by its hash."""
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return RefreshTokenMapper.to_entity(model) if model else None

    async def save(self, refresh_token: RefreshToken) -> RefreshToken:
        """Save new refresh token."""
        model = RefreshTokenMapper.to_model(refresh_token)
        self.session.add(model)
        await self.session.flush()
        return RefreshTokenMapper.to_entity(model)

    async def update(self, refresh_token: RefreshToken) -> RefreshToken:
        """Update existing refresh token."""
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.id == refresh_token.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        RefreshTokenMapper.update_model(model, refresh_token)
        await self.session.flush()
        return RefreshTokenMapper.to_entity(model)

    async def revoke_by_token_hash(self, token_hash: str, revoked_at: datetime) -> None:
        """Revoke refresh token by hash."""
        stmt = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.token_hash == token_hash)
            .values(revoked_at=revoked_at)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def revoke_all_for_user(self, user_id: UUID, revoked_at: datetime) -> None:
        """Revoke all refresh tokens for a user."""
        stmt = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def revoke_family(self, family_id: UUID, revoked_at: datetime) -> None:
        """Revoke all refresh tokens in a family (for reuse detection)."""
        stmt = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.family_id == family_id,
                RefreshTokenModel.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def delete_expired(self, before: datetime) -> int:
        """Delete expired tokens (cleanup). Returns number deleted."""
        stmt = delete(RefreshTokenModel).where(RefreshTokenModel.expires_at < before)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount  # type: ignore
