"""Update product use case."""

from app.application.dto.product_dto import UpdateProductRequest, ProductDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.domain.errors.domain_errors import ProductNotFoundError


class UpdateProductUseCase:
    """Use case for updating an existing product."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: ClockPort,
        audit_log: AuditLogPort,
    ) -> None:
        self.uow = uow
        self.clock = clock
        self.audit_log = audit_log

    async def execute(self, request: UpdateProductRequest) -> ProductDTO:
        """
        Update product details.
        
        Raises:
            ResourceNotFoundError: If product not found
        """
        async with self.uow:
            # Get existing product
            product = await self.uow.products.get_by_id(request.product_id)
            if not product:
                raise ResourceNotFoundError(f"Product {request.product_id} not found")

            # Update product
            now = self.clock.now()
            updated_product = product.update_details(
                name=request.name,
                description_short=request.description_short,
                description_long=request.description_long,
                tags=request.tags,
                featured=request.featured,
                sort_order=request.sort_order,
                updated_at=now,
                updated_by=request.updated_by,
            )

            # Save
            updated_product = await self.uow.products.update(updated_product)
            await self.uow.commit()

            # Audit log
            await self.audit_log.log_event(
                event_type="product.updated",
                user_id=request.updated_by,
                details={
                    "product_id": str(updated_product.id),
                    "name": updated_product.name,
                },
            )

            return ProductDTO(
                id=updated_product.id,
                status=updated_product.status.value,
                name=updated_product.name,
                slug=str(updated_product.slug),
                description_short=updated_product.description_short,
                description_long=updated_product.description_long,
                tags=updated_product.tags,
                featured=updated_product.featured,
                sort_order=updated_product.sort_order,
                created_at=updated_product.created_at,
                updated_at=updated_product.updated_at,
                created_by=updated_product.created_by,
                updated_by=updated_product.updated_by,
            )
