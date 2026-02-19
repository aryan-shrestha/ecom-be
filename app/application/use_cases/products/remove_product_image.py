"""Remove product image use case."""

from typing import Optional
from uuid import UUID

from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.cache_port import CachePort


class RemoveProductImageUseCase:
    """Use case for removing an image from a product."""

    def __init__(
        self,
        uow: UnitOfWork,
        audit_log: AuditLogPort,
        cache: CachePort,
    ) -> None:
        self.uow = uow
        self.audit_log = audit_log
        self.cache = cache

    async def execute(self, product_id: UUID, image_id: UUID, removed_by: Optional[UUID] = None) -> None:
        """
        Remove image from product.
        
        Raises:
            ResourceNotFoundError: If image not found
        """
        async with self.uow:
            # Get image
            image = await self.uow.products.get_image_by_id(image_id)
            if not image or image.product_id != product_id:
                raise ResourceNotFoundError(f"Image {image_id} not found for product {product_id}")

            # Delete image
            await self.uow.products.delete_image(image_id)
            await self.uow.commit()

            # Invalidate cache
            await self.cache.delete(f"product:{product_id}")
            await self.cache.delete_pattern("products:storefront:*")

            # Audit log
            await self.audit_log.log_event(
                event_type="product.image.removed",
                user_id=removed_by,
                details={
                    "product_id": str(product_id),
                    "image_id": str(image_id),
                },
            )
