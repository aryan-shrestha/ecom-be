from app.application.dto.permission_dto import PermissionDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork

class GetPermissionForRoleUseCase:
    """Use case for getting permissions for a role."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, role_name: str) -> list[PermissionDTO]:
        """
        Get permissions for a role by name.
        
        Raises:
            ResourceNotFoundError: If role not found
        """
        async with self.uow:
            role = await self.uow.rbac.get_role_by_name(name=role_name)

            if not role:
                raise ResourceNotFoundError(f"Role {role_name} not found")
            
            permissions = await self.uow.rbac.get_permissions_for_roles(role_names=[role_name])
            
            return [
                PermissionDTO(
                    id=permission.id,
                    code=permission.code,
                )
                for permission in permissions
            ]

