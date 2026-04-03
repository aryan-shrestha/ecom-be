import uuid

from app.application.dto.role_dto import RoleDTO
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.domain.entities.role import Role


class CreateRoleUseCase:
    """
    Use case for creating a new role.
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

    async def execute(self, name: str, user_id: uuid.UUID) -> RoleDTO:
        """
        Create a new role with the given name.
        
        Raises:
            ValueError: If role with the same name already exists
        """
        async with self.uow:
            # Check if role already exists
            existing_role = await self.uow.rbac.get_role_by_name(name=name)
            if existing_role:
                raise ValueError(f"Role with name {name} already exists")

            # Create new role entity
            role = Role(
                id=uuid.uuid4(),
                name=name,
            )

            # Save to database
            await self.uow.rbac.create_role(role)

            # Log creation event
            await self.audit_log.log_event(
                event_type="role.created",
                user_id=user_id,
                details={
                    "role_id": str(role.id), 
                    "name": role.name, 
                },
            )

            return RoleDTO(
                id=role.id,
                name=role.name,
            )