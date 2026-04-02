from uuid import UUID
from app.application.interfaces.uow import UnitOfWork
from app.application.dto.role_dto import RoleDTO, RoleListDTO

class GetUserRolesUseCase:
    """
    Use case for getting user roles.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, user_id: UUID) -> list[str]:
        """
        Get user roles.

        Args:
            user_id (UUID): ID of the user to retrieve roles for.

        Returns:
            list[str]: List of role names assigned to the user.
        """
        async with self.uow:
            roles = await self.uow.auth.get_user_roles(user_id)
            role_dtos = [
                RoleDTO(
                    id=role.id,
                    name=role.name
                    ) 
                    for role in roles
                ]
            return RoleListDTO(roles=role_dtos)
                
            