from typing import Optional
from uuid import UUID

from app.application.dto.user_dto import UserDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort


class DeactivateUserAdminUseCase:
    """
    Use case for deactivating a user by admin.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: ClockPort,
        audit_log: AuditLogPort,
    ) -> None:
        self.uow = uow
        self.clock = clock
        self.audit_log = audit_log    
    
    async def execute(self, user_id: UUID, deactivated_by: Optional[UUID] = None) -> UserDTO:
        """
        Deactivate user by admin.

        Raises:
            ResourceNotFoundError: If user not found
        """

        async with self.uow:
            user = await self.uow.users.get_by_id(user_id=user_id)

            if not user:
                raise ResourceNotFoundError(f"User {user_id} not found")
            
            now = self.clock.now()
            deactivated_user = user.deactivate(updated_at=now)

            deactivated_user = await self.uow.users.update(deactivated_user)
            await self.uow.commit()

            await self.audit_log.log_event(
                event_type="user.deactivated",
                user_id=deactivated_by,
                details={
                    "user_id": str(deactivated_user.id),
                    "email": str(deactivated_user.email),
                }
            )

            return UserDTO(
                id=deactivated_user.id,
                email=deactivated_user.email,
                first_name=deactivated_user.first_name,
                last_name=deactivated_user.last_name,
                is_active=deactivated_user.is_active,
                is_verified=deactivated_user.is_verified,
                created_at=deactivated_user.created_at,
                updated_at=deactivated_user.updated_at,
            )
            
