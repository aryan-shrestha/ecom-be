"""
Add size use case
"""
import uuid
from app.application.dto.size_dto import SizeDTO, SizeCreateRequest
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.domain.entities.product import Product
from app.domain.entities.size import Size

class AddSizeUseCase:
    """
    Use case for adding a size to a product
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
    
    async def execute(self, request: SizeCreateRequest) -> SizeDTO:
        """
        Add size to product.

        Raises:
            ResourceNotFoundError: If product not found
        """
        async with self.uow:
            # Check product exists
            product = await self.uow.products.get_by_id(request.product_id)
            if not product:
                raise ResourceNotFoundError(f"Product {request.product_id} not found")

            # Create size
            now = self.clock.now()
            size = Size(
                id=uuid.uuid4(),
                name=request.name,
                product_id=request.product_id,
                created_at=now,
                updated_at=now,
            )
            size = await self.uow.sizes.save(size)

            return SizeDTO(
                id=size.id,
                product_id=size.product_id,
                name=size.name,
                created_at=size.created_at,
                updated_at=size.updated_at,
            )