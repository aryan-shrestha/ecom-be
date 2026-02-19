"""Publish product use case."""

from typing import Optional
from uuid import UUID

from app.application.dto.product_dto import ProductDTO
from app.application.errors.app_errors import ResourceNotFoundError, ValidationError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.cache_port import CachePort
from app.application.ports.clock_port import ClockPort
from app.domain.entities.product_variant import VariantStatus
from app.domain.errors.domain_errors import ProductPublishError
from app.domain.policies.product_publish_policy import ProductPublishPolicy


class PublishProductUseCase:
    """Use case for publishing a product."""

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

    async def execute(self, product_id: UUID, published_by: Optional[UUID] = None) -> ProductDTO:
        """
        Publish product.
        
        Validates business rules before publishing.
        
        Raises:
            ResourceNotFoundError: If product not found
            ValidationError: If product cannot be published
        """
        async with self.uow:
            # Get product
            product = await self.uow.products.get_by_id(product_id)
            if not product:
                raise ResourceNotFoundError(f"Product {product_id} not found")

            # Get variants
            variants = await self.uow.products.get_variants_for_product(product_id)

            # Validate publish policy
            variant_info = []
            for variant in variants:
                has_valid_pricing = variant.price.amount > 0 and variant.sku.value != ""
                variant_info.append((variant, variant.status, has_valid_pricing))

            try:
                ProductPublishPolicy.ensure_can_publish(product, variant_info)
            except ProductPublishError as e:
                raise ValidationError(str(e))

            # Publish product
            now = self.clock.now()
            published_product = product.publish(now, published_by)

            # Save
            published_product = await self.uow.products.update(published_product)
            await self.uow.commit()

            # Invalidate cache
            await self.cache.delete(f"product:{product_id}")
            await self.cache.delete(f"product:slug:{product.slug}")
            await self.cache.delete_pattern("products:storefront:*")

            # Audit log
            await self.audit_log.log_event(
                event_type="product.published",
                user_id=published_by,
                details={
                    "product_id": str(published_product.id),
                    "name": published_product.name,
                },
            )

            return ProductDTO(
                id=published_product.id,
                status=published_product.status.value,
                name=published_product.name,
                slug=str(published_product.slug),
                description_short=published_product.description_short,
                description_long=published_product.description_long,
                tags=published_product.tags,
                featured=published_product.featured,
                sort_order=published_product.sort_order,
                created_at=published_product.created_at,
                updated_at=published_product.updated_at,
                created_by=published_product.created_by,
                updated_by=published_product.updated_by,
            )
