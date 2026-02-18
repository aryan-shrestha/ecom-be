"""Assign role to user use case."""

from uuid import UUID

from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.domain.errors.domain_errors import RoleNotFoundError, UserNotFoundError


class AssignRoleUseCase:
    """Use case for assigning role to user."""

    def __init__(
        self,
        uow: UnitOfWork,
        audit_log: AuditLogPort,
    ) -> None:
        self.uow = uow
        self.audit_log = audit_log

    async def execute(self, user_id: UUID, role_name: str) -> None:
        """
        Assign role to user.
        
        Raises:
            UserNotFoundError: If user not found
            RoleNotFoundError: If role not found
        """
        async with self.uow:
            # Verify user exists
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User {user_id} not found")

            # Verify role exists
            role = await self.uow.rbac.get_role_by_name(role_name)
            if not role:
                raise RoleNotFoundError(f"Role '{role_name}' not found")

            # Assign role
            await self.uow.auth.assign_role_to_user(user_id, role_name)
            await self.uow.commit()

            # Audit
            await self.audit_log.log_event(
                event_type="rbac.role_assigned",
                user_id=user_id,
                details={"role": role_name},
            )
