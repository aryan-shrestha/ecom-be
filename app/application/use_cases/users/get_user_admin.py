"""Get user details for admin use case."""
from uuid import UUID

from app.application.dto.user_dto import UserDTO
from app.application.dto.role_dto import RoleDTO, RoleListDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork

class GetUserAdminUseCase:
    """
    Use case for getting user details for admin.
    """
    
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
    
    async def execute(self, user_id: UUID) -> UserDTO:
        """
        Get user details for admin.
        
        Args:
            user_id (UUID): ID of the user to retrieve.
        
        Returns:
            UserDTO: User details.
        
        Raises:
            ResourceNotFoundError: If user not found.
        """
        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)

            if not user:
                raise ResourceNotFoundError(f"User {user_id} not found")
            

            roles = await self.uow.auth.get_user_roles(user_id)
            role_list_dto = RoleListDTO(
                roles=[
                    RoleDTO(
                        id=role.id,
                        name=role.name  
                    ) 
                    for role in roles
                ]
            )
            
            return UserDTO(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
                roles=role_list_dto
            )