import uuid

from app.application.dto.permission_dto import PermissionDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort


class AssignPermissionToRoleUseCase:
    """Use case for assigning permission to a role."""

    def __init__(self, uow: UnitOfWork, audit_log: AuditLogPort) -> None:
        self.uow = uow
        self.audit_log = audit_log

    async def execute(self, role_name: str, permission_code: str, user_id: uuid.UUID) -> bool:
        """
        Assign a permission to a role by name and code.
        
        Raises:
            ResourceNotFoundError: If role or permission not found
        """
        async with self.uow:
            role = await self.uow.rbac.get_role_by_name(name=role_name)
            if not role:
                raise ResourceNotFoundError(f"Role {role_name} not found")

            permission = await self.uow.rbac.get_permission_by_code(code=permission_code)
            if not permission:
                raise ResourceNotFoundError(f"Permission {permission_code} not found")

            await self.uow.rbac.assign_permission_to_role(role_name=role_name, permission_code=permission_code)
            await self.uow.commit()

            await self.audit_log.log_event(
                event_type="permission.assigned_to_role",
                user_id=str(user_id),
                details={
                    "role_name": role_name, 
                    "permission_code": permission_code,
                },
            )

            return True