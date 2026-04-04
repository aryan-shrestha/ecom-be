"""
List permissions use case for RBAC (Role-Based Access Control) system.
"""
from app.application.dto.permission_dto import PermissionDTO, PermissionListDTO
from app.application.interfaces.uow import UnitOfWork
from app.domain.entities.permission import Permission

class ListPermissionsUseCase:
    """
    Use case for listing permissions.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self) -> PermissionListDTO:
        """
        List permissions with pagination.
        """
        async with self.uow:
            permissions = await self.uow.rbac.list_all_permissions()

            permission_dtos = [PermissionDTO(id=p.id, code=p.code) for p in permissions]

            return PermissionListDTO(permissions=permission_dtos)