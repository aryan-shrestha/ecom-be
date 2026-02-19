"""Reorder product images use case."""

from app.application.dto.product_dto import ReorderImagesRequest
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.cache_port import CachePort


class ReorderProductImagesUseCase:
    """Use case for reordering product images."""

    def __init__(
        self,
        uow: UnitOfWork,
        audit_log: AuditLogPort,
        cache: CachePort,
    ) -> None:
        self.uow = uow
        self.audit_log = audit_log
        self.cache = cache

    async def execute(self, request: ReorderImagesRequest) -> None:
        """
        Reorder product images.
        
        Raises:
            ResourceNotFoundError: If product not found
        """
        async with self.uow:
            # Check product exists
            product = await self.uow.products.get_by_id(request.product_id)
            if not product:
                raise ResourceNotFoundError(f"Product {request.product_id} not found")

            # Reorder images
            await self.uow.products.reorder_images(request.product_id, request.image_positions)
            await self.uow.commit()

            # Invalidate cache
            await self.cache.delete(f"product:{request.product_id}")
            await self.cache.delete_pattern("products:storefront:*")

            # Audit log
            await self.audit_log.log_event(
                event_type="product.images.reordered",
                user_id=None,
                details={
                    "product_id": str(request.product_id),
                },
            )
