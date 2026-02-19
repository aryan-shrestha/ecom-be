"""Archive product use case."""

from typing import Optional
from uuid import UUID

from app.application.dto.product_dto import ProductDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.cache_port import CachePort
from app.application.ports.clock_port import ClockPort


class ArchiveProductUseCase:
    """Use case for archiving a product."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: ClockPort,
        audit_log: AuditLogPort,
        cache: CachePort,
    ) -> None:
        self.uow = uow
        self.clock = clock
        self.audit_log = audit_log
        self.cache = cache

    async def execute(self, product_id: UUID, archived_by: Optional[UUID] = None) -> ProductDTO:
        """
        Archive product (soft delete).
        
        Raises:
            ResourceNotFoundError: If product not found
        """
        async with self.uow:
            # Get product
            product = await self.uow.products.get_by_id(product_id)
            if not product:
                raise ResourceNotFoundError(f"Product {product_id} not found")

            # Archive product
            now = self.clock.now()
            archived_product = product.archive(now, archived_by)

            # Save
            archived_product = await self.uow.products.update(archived_product)
            await self.uow.commit()

            # Invalidate cache
            await self.cache.delete(f"product:{product_id}")
            await self.cache.delete(f"product:slug:{product.slug}")
            await self.cache.delete_pattern("products:storefront:*")

            # Audit log
            await self.audit_log.log_event(
                event_type="product.archived",
                user_id=archived_by,
                details={
                    "product_id": str(archived_product.id),
                    "name": archived_product.name,
                },
            )

            return ProductDTO(
                id=archived_product.id,
                status=archived_product.status.value,
                name=archived_product.name,
                slug=str(archived_product.slug),
                description_short=archived_product.description_short,
                description_long=archived_product.description_long,
                tags=archived_product.tags,
                featured=archived_product.featured,
                sort_order=archived_product.sort_order,
                created_at=archived_product.created_at,
                updated_at=archived_product.updated_at,
                created_by=archived_product.created_by,
                updated_by=archived_product.updated_by,
            )
