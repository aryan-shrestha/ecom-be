"""SQLAlchemy implementation of UserRepository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.email import Email
from app.infrastructure.db.sqlalchemy.models.user_model import UserModel
from app.infrastructure.mappers.user_mapper import UserMapper


class SqlAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Retrieve user by ID."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_entity(model) if model else None

    async def get_by_email(self, email: Email) -> Optional[User]:
        """Retrieve user by email."""
        stmt = select(UserModel).where(UserModel.email == str(email))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_entity(model) if model else None

    async def exists_by_email(self, email: Email) -> bool:
        """Check if user exists with given email."""
        stmt = select(UserModel.id).where(UserModel.email == str(email))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def save(self, user: User) -> User:
        """Save new user (insert)."""
        model = UserMapper.to_model(user)
        self.session.add(model)
        await self.session.flush()
        return UserMapper.to_entity(model)

    async def update(self, user: User) -> User:
        """Update existing user."""
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        UserMapper.update_model(model, user)
        await self.session.flush()
        return UserMapper.to_entity(model)

    async def delete(self, user_id: UUID) -> None:
        """Delete user by ID."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()
