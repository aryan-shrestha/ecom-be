"""SQLAlchemy implementation of RbacRepository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.repositories.rbac_repository import RbacRepository
from app.infrastructure.db.sqlalchemy.models.permission_model import PermissionModel
from app.infrastructure.db.sqlalchemy.models.role_model import RoleModel
from app.infrastructure.db.sqlalchemy.models.role_permission_model import RolePermissionModel


class SqlAlchemyRbacRepository(RbacRepository):
    """SQLAlchemy implementation of RbacRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        stmt = select(RoleModel).where(RoleModel.name == name)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return Role(id=model.id, name=model.name) if model else None

    async def get_permission_by_code(self, code: str) -> Optional[Permission]:
        """Get permission by code."""
        stmt = select(PermissionModel).where(PermissionModel.code == code)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return Permission(id=model.id, code=model.code) if model else None

    async def get_permissions_for_roles(self, role_names: list[str]) -> list[Permission]:
        """Get all permissions associated with given roles."""
        if not role_names:
            return []

        stmt = (
            select(PermissionModel)
            .join(RolePermissionModel, RolePermissionModel.permission_id == PermissionModel.id)
            .join(RoleModel, RoleModel.id == RolePermissionModel.role_id)
            .where(RoleModel.name.in_(role_names))
            .distinct()
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [Permission(id=model.id, code=model.code) for model in models]

    async def create_role(self, role: Role) -> Role:
        """Create new role."""
        model = RoleModel(id=role.id, name=role.name)
        self.session.add(model)
        await self.session.flush()
        return Role(id=model.id, name=model.name)

    async def create_permission(self, permission: Permission) -> Permission:
        """Create new permission."""
        model = PermissionModel(id=permission.id, code=permission.code)
        self.session.add(model)
        await self.session.flush()
        return Permission(id=model.id, code=model.code)

    async def assign_permission_to_role(self, role_name: str, permission_code: str) -> None:
        """Assign permission to role."""
        # Get role and permission IDs
        role_stmt = select(RoleModel.id).where(RoleModel.name == role_name)
        perm_stmt = select(PermissionModel.id).where(PermissionModel.code == permission_code)

        role_result = await self.session.execute(role_stmt)
        perm_result = await self.session.execute(perm_stmt)

        role_id = role_result.scalar_one()
        permission_id = perm_result.scalar_one()

        # Check if already assigned
        check_stmt = select(RolePermissionModel).where(
            RolePermissionModel.role_id == role_id,
            RolePermissionModel.permission_id == permission_id,
        )
        check_result = await self.session.execute(check_stmt)
        if check_result.scalar_one_or_none():
            return  # Already assigned

        # Assign
        role_permission = RolePermissionModel(role_id=role_id, permission_id=permission_id)
        self.session.add(role_permission)
        await self.session.flush()

    async def list_all_roles(self) -> list[Role]:
        """List all roles."""
        stmt = select(RoleModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [Role(id=model.id, name=model.name) for model in models]

    async def list_all_permissions(self) -> list[Permission]:
        """List all permissions."""
        stmt = select(PermissionModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [Permission(id=model.id, code=model.code) for model in models]
