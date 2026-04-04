import uuid
from app.application.dto.permission_dto import PermissionDTO
from app.application.interfaces.uow import UnitOfWork 
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.domain.entities.permission import Permission


class CreatePermissionUseCase:
    """
    Use case for creating a new permission
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

    async def execute(self, code: str, user_id: uuid.UUID) -> PermissionDTO:
        """
        Create a new permission with the given code.
        
        Raises:
            ValueError: If permission with the same code already exists
        """
        async with self.uow:
            # Check if permission already exists
            existing_permission = await self.uow.rbac.get_permission_by_code(code=code)
            if existing_permission:
                raise ValueError(f"Permission with code {code} already exists")

            # Create new permission entity
            permission = Permission(
                id=uuid.uuid4(),
                code=code,
            )

            # Save to database
            await self.uow.rbac.create_permission(permission)

            # Log creation event
            await self.audit_log.log_event(
                event_type="permission.created",
                user_id=user_id,
                details={
                    "permission_id": str(permission.id), 
                    "code": permission.code, 
                },
            )

            return PermissionDTO(
                id=permission.id,
                code=permission.code,
            )