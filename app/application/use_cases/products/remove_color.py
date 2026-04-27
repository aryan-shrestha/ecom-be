from uuid import UUID

from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.cache_port import CachePort


class RemoveColorUseCase:

    def __init__(
        self,
        uow: UnitOfWork,
        audit_log: AuditLogPort,
        cache: CachePort,
    ) -> None:
        self.uow = uow
        self.audit_log = audit_log
        self.cache = cache
    
    async def execute(self, color_id: UUID) -> None:
        """
        Remove color.

        Raises:
            ResourceNotFoundError: If color not found
        """
        async with self.uow:
            # Get color
            color = await self.uow.colors.get_by_id(color_id)
            if not color:
                raise ResourceNotFoundError(f"Color {color_id} not found")

            # Delete color
            await self.uow.colors.delete(color_id)
            await self.uow.commit()

            # Invalidate cache
            await self.cache.delete_pattern("products:storefront:*")