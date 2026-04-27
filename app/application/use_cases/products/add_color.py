"""
Add color use case
"""
import uuid
from app.application.dto.color_dto import ColorDTO, ColorCreateRequest
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.domain.entities.color import Color
from app.domain.entities.product import Product


class AddColorUseCase:
    """"
    Use case for adding a color to a product
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
    
    async def execute(self, request: ColorCreateRequest) -> ColorDTO:
        """
        Add color to product.

        Raises:
            ResourceNotFoundError: If product not found
        """
        async with self.uow:
            # Check product exists
            product = await self.uow.products.get_by_id(request.product_id)
            if not product:
                raise ResourceNotFoundError(f"Product {request.product_id} not found")

            # Create color
            now = self.clock.now()
            color = Color(
                id=uuid.uuid4(),
                name=request.name,
                hex_value=request.hex_value,
                product_id=request.product_id,
                created_at=now,
                updated_at=now,
            )
            color = await self.uow.colors.save(color)

            return ColorDTO(
                id=color.id,
                product_id=color.product_id,
                name=color.name,
                hex_value=color.hex_value,
                created_at=color.created_at,
                updated_at=color.updated_at,
            )