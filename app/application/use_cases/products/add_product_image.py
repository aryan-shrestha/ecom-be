"""Add product image use case."""

import uuid

from app.application.dto.product_dto import AddProductImageRequest, ProductImageDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.cache_port import CachePort
from app.application.ports.clock_port import ClockPort
from app.domain.entities.product_image import ProductImage


class AddProductImageUseCase:
    """Use case for adding an image to a product."""

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

    async def execute(self, request: AddProductImageRequest) -> ProductImageDTO:
        """
        Add image to product.
        
        Raises:
            ResourceNotFoundError: If product not found
        """
        async with self.uow:
            # Check product exists
            product = await self.uow.products.get_by_id(request.product_id)
            if not product:
                raise ResourceNotFoundError(f"Product {request.product_id} not found")

            # Get existing images to determine position
            existing_images = await self.uow.products.get_images_for_product(request.product_id)
            next_position = len(existing_images)

            # Create image
            now = self.clock.now()
            image = ProductImage(
                id=uuid.uuid4(),
                product_id=request.product_id,
                url=request.url,
                alt_text=request.alt_text,
                position=next_position,
                created_at=now,
            )

            # Save
            image = await self.uow.products.save_image(image)
            await self.uow.commit()

            # Invalidate cache
            await self.cache.delete(f"product:{request.product_id}")
            await self.cache.delete_pattern("products:storefront:*")

            # Audit log
            await self.audit_log.log_event(
                event_type="product.image.added",
                user_id=None,
                details={
                    "product_id": str(request.product_id),
                    "image_id": str(image.id),
                },
            )

            return ProductImageDTO(
                id=image.id,
                product_id=image.product_id,
                url=image.url,
                alt_text=image.alt_text,
                position=image.position,
                created_at=image.created_at,
            )
