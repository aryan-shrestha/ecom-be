"""SQLAlchemy implementation of AuthRepository."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.auth_repository import AuthRepository
from app.infrastructure.db.sqlalchemy.models.role_model import RoleModel
from app.infrastructure.db.sqlalchemy.models.user_role_model import UserRoleModel


class SqlAlchemyAuthRepository(AuthRepository):
    """SQLAlchemy implementation of AuthRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_roles(self, user_id: UUID) -> list[str]:
        """Get list of role names assigned to user."""
        stmt = (
            select(RoleModel.name)
            .join(UserRoleModel, UserRoleModel.role_id == RoleModel.id)
            .where(UserRoleModel.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def assign_role_to_user(self, user_id: UUID, role_name: str) -> None:
        """Assign role to user."""
        # Get role ID
        stmt = select(RoleModel.id).where(RoleModel.name == role_name)
        result = await self.session.execute(stmt)
        role_id = result.scalar_one()

        # Check if already assigned
        check_stmt = select(UserRoleModel).where(
            UserRoleModel.user_id == user_id, UserRoleModel.role_id == role_id
        )
        check_result = await self.session.execute(check_stmt)
        if check_result.scalar_one_or_none():
            return  # Already assigned

        # Assign
        user_role = UserRoleModel(user_id=user_id, role_id=role_id)
        self.session.add(user_role)
        await self.session.flush()

    async def remove_role_from_user(self, user_id: UUID, role_name: str) -> None:
        """Remove role from user."""
        # Get role ID
        stmt = select(RoleModel.id).where(RoleModel.name == role_name)
        result = await self.session.execute(stmt)
        role_id = result.scalar_one_or_none()
        if not role_id:
            return  # Role doesn't exist

        # Delete association
        delete_stmt = delete(UserRoleModel).where(
            UserRoleModel.user_id == user_id, UserRoleModel.role_id == role_id
        )
        await self.session.execute(delete_stmt)
        await self.session.flush()
