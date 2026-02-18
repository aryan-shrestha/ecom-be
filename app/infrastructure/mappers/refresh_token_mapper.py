"""Refresh token mapper - converts between ORM models and domain entities."""

from app.domain.entities.refresh_token import RefreshToken
from app.infrastructure.db.sqlalchemy.models.refresh_token_model import RefreshTokenModel


class RefreshTokenMapper:
    """Mapper for RefreshToken entity and RefreshTokenModel."""

    @staticmethod
    def to_entity(model: RefreshTokenModel) -> RefreshToken:
        """Convert ORM model to domain entity."""
        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            family_id=model.family_id,
            issued_at=model.issued_at,
            expires_at=model.expires_at,
            revoked_at=model.revoked_at,
            replaced_by_token_id=model.replaced_by_token_id,
            ip=model.ip,
            user_agent=model.user_agent,
        )

    @staticmethod
    def to_model(entity: RefreshToken) -> RefreshTokenModel:
        """Convert domain entity to ORM model."""
        return RefreshTokenModel(
            id=entity.id,
            user_id=entity.user_id,
            token_hash=entity.token_hash,
            family_id=entity.family_id,
            issued_at=entity.issued_at,
            expires_at=entity.expires_at,
            revoked_at=entity.revoked_at,
            replaced_by_token_id=entity.replaced_by_token_id,
            ip=entity.ip,
            user_agent=entity.user_agent,
        )

    @staticmethod
    def update_model(model: RefreshTokenModel, entity: RefreshToken) -> None:
        """Update existing ORM model from domain entity."""
        model.token_hash = entity.token_hash
        model.revoked_at = entity.revoked_at
        model.replaced_by_token_id = entity.replaced_by_token_id
