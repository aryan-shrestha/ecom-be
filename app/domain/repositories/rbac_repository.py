"""RBAC repository interface."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role


class RbacRepository(ABC):
    """Repository interface for RBAC (roles and permissions)."""

    @abstractmethod
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        ...

    @abstractmethod
    async def get_permission_by_code(self, code: str) -> Optional[Permission]:
        """Get permission by code."""
        ...

    @abstractmethod
    async def get_permissions_for_roles(self, role_names: list[str]) -> list[Permission]:
        """Get all permissions associated with given roles."""
        ...

    @abstractmethod
    async def create_role(self, role: Role) -> Role:
        """Create new role."""
        ...

    @abstractmethod
    async def create_permission(self, permission: Permission) -> Permission:
        """Create new permission."""
        ...

    @abstractmethod
    async def assign_permission_to_role(self, role_name: str, permission_code: str) -> None:
        """Assign permission to role."""
        ...

    @abstractmethod
    async def list_all_roles(self) -> list[Role]:
        """List all roles."""
        ...

    @abstractmethod
    async def list_all_permissions(self) -> list[Permission]:
        """List all permissions."""
        ...
