"""Create product use case."""

import uuid

from app.application.dto.product_dto import CreateProductRequest, ProductDTO
from app.application.errors.app_errors import ConflictError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.domain.entities.product import Product, ProductStatus
from app.domain.value_objects.slug import Slug


class CreateProductUseCase:
    """Use case for creating a new product."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: ClockPort,
        audit_log: AuditLogPort,
    ) -> None:
        self.uow = uow
        self.clock = clock
        self.audit_log = audit_log

    async def execute(self, request: CreateProductRequest) -> ProductDTO:
        """
        Create new product.
        
        Raises:
            ConflictError: If product with slug already exists
        """
        slug = Slug.from_string(request.slug)

        async with self.uow:
            # Check if product with slug exists
            if await self.uow.products.exists_by_slug(slug):
                raise ConflictError(f"Product with slug '{slug}' already exists")

            # Create product entity
            now = self.clock.now()
            product = Product(
                id=uuid.uuid4(),
                status=ProductStatus.DRAFT,
                name=request.name,
                slug=slug,
                description_short=request.description_short,
                description_long=request.description_long,
                tags=request.tags,
                featured=request.featured,
                sort_order=request.sort_order,
                created_at=now,
                updated_at=now,
                created_by=request.created_by,
                updated_by=request.created_by,
            )

            # Save product
            product = await self.uow.products.save(product)
            await self.uow.commit()

            # Audit log
            await self.audit_log.log_event(
                event_type="product.created",
                user_id=request.created_by,
                details={
                    "product_id": str(product.id),
                    "name": product.name,
                    "slug": str(product.slug),
                },
            )

            return ProductDTO(
                id=product.id,
                status=product.status.value,
                name=product.name,
                slug=str(product.slug),
                description_short=product.description_short,
                description_long=product.description_long,
                tags=product.tags,
                featured=product.featured,
                sort_order=product.sort_order,
                created_at=product.created_at,
                updated_at=product.updated_at,
                created_by=product.created_by,
                updated_by=product.updated_by,
            )
