"""Get role details use case."""

from app.application.dto.role_dto import RoleDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork

class GetRoleDetailUseCase:
    """Use case for getting role details."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, role_name: str) -> RoleDTO:
        """
        Get role details by name.
        
        Raises:
            ResourceNotFoundError: If role not found
        """
        async with self.uow:
            role = await self.uow.rbac.get_role_by_name(name=role_name)
            
            if not role:
                raise ResourceNotFoundError(f"Role {role_name} not found")

            return RoleDTO(
                id=role.id,
                name=role.name,
            
            )