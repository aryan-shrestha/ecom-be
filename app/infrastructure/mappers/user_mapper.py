"""User mapper - converts between ORM models and domain entities."""

from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.infrastructure.db.sqlalchemy.models.user_model import UserModel


class UserMapper:
    """Mapper for User entity and UserModel."""

    @staticmethod
    def to_entity(model: UserModel) -> User:
        """Convert ORM model to domain entity."""
        return User(
            id=model.id,
            email=Email(model.email),
            password_hash=model.password_hash,
            is_active=model.is_active,
            is_verified=model.is_verified,
            token_version=model.token_version,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: User) -> UserModel:
        """Convert domain entity to ORM model."""
        return UserModel(
            id=entity.id,
            email=str(entity.email),
            password_hash=entity.password_hash,
            is_active=entity.is_active,
            is_verified=entity.is_verified,
            token_version=entity.token_version,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def update_model(model: UserModel, entity: User) -> None:
        """Update existing ORM model from domain entity."""
        model.email = str(entity.email)
        model.password_hash = entity.password_hash
        model.is_active = entity.is_active
        model.is_verified = entity.is_verified
        model.token_version = entity.token_version
        model.updated_at = entity.updated_at
