from uuid import UUID

from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.cache_port import CachePort


class RemoveSizeUseCase:
    
    def __init__(
        self,
        uow: UnitOfWork,
        audit_log: AuditLogPort,
        cache: CachePort,
    ) -> None:
        self.uow = uow
        self.audit_log = audit_log
        self.cache = cache
    
    async def execute(self, size_id: UUID) -> None:
        """
        Remove size.

        Raises:
            ResourceNotFoundError: If size not found
        """
        async with self.uow:
            # Get size
            size = await self.uow.sizes.get_by_id(size_id)
            if not size:
                raise ResourceNotFoundError(f"Size {size_id} not found")

            # Delete size
            await self.uow.sizes.delete(size_id)
            await self.uow.commit()

            # Invalidate cache
            await self.cache.delete_pattern("products:storefront:*")