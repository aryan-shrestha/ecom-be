from app.application.dto.role_dto import RoleDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort


class DeletePermissionUseCase:
    """
    Use case for deleting a permission.

    Raise:
        ResourceNotFoundError: If permission not found
    """

    def __init__(self, uow: UnitOfWork, audit_log: AuditLogPort) -> None:
        self.uow = uow
        self.audit_log = audit_log

    async def execute(self, permission_code: str, user_id: str) -> RoleDTO:
        """
        Delete a permission by code.
        
        Raises:
            ResourceNotFoundError: If permission not found
        """
        async with self.uow:
            permission = await self.uow.rbac.get_permission_by_code(permission_code)

            if not permission:
                raise ResourceNotFoundError(f"Permission {permission_code} not found")
            
            await self.uow.rbac.delete_permission(permission_code)
            await self.uow.commit()

            await self.audit_log.log_event(
                event_type="permission.deleted",
                user_id=user_id,
                details={
                    "permission_code": permission_code, 
                    "permission_id": str(permission.id)
                },
            )
            
            if not permission:
                raise ResourceNotFoundError(f"Permission {permission_code} not found")

            return True