from app.application.dto.role_dto import RoleDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort

class DeleteRoleUseCase:
    """Use case for deleting a role."""

    def __init__(self, uow: UnitOfWork, audit_log: AuditLogPort) -> None:
        self.uow = uow
        self.audit_log = audit_log

    async def execute(self, role_name: str, user_id: str) -> RoleDTO:
        """
        Delete a role by name.
        
        Raises:
            ResourceNotFoundError: If role not found
        """
        async with self.uow:
            role = await self.uow.rbac.get_role_by_name(role_name)

            if not role:
                raise ResourceNotFoundError(f"Role {role_name} not found")
            
            await self.uow.rbac.delete_role(role_name)
            await self.uow.commit()

            await self.audit_log.log_event(
                event_type="role.deleted",
                user_id=user_id,
                details={
                    "role_name": role_name, 
                    "role_id": str(role.id)
                },
            )
            
            if not role:
                raise ResourceNotFoundError(f"Role {role_name} not found")

            return True