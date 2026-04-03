"""
List roles use case
"""
from app.application.dto.role_dto import RoleDTO, RoleListDTO
from app.application.interfaces.uow import UnitOfWork
from app.domain.entities.role import Role

class ListRolesUseCase:
    """
    Use case for listing roles.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self) -> RoleListDTO:
        """
        List roles with pagination.
        """
        async with self.uow:
            roles = await self.uow.rbac.list_all_roles()

            role_dtos = [RoleDTO(id=r.id, name=r.name) for r in roles]

            return RoleListDTO(roles=role_dtos)
