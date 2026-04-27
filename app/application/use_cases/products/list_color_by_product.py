import uuid
from app.application.dto.color_dto import ColorDTO
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.application.errors.app_errors import ResourceNotFoundError
from app.domain.entities.color import Color
from app.domain.entities.product import Product


class ListColorByProductUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow
    
    async def execute(self, product_id: uuid.UUID) -> list[ColorDTO]:
        """
        List colors by product.

        Raises:
            ResourceNotFoundError: If product not found
        """
        async with self.uow:
            # Check product exists
            product = await self.uow.products.get_by_id(product_id)
            if not product:
                raise ResourceNotFoundError(f"Product {product_id} not found")

            colors = await self.uow.colors.list_by_product_id(product_id)

            return [
                ColorDTO(
                    name=color.name,
                    hex_value=color.hex_value,
                    created_at=color.created_at,
                    updated_at=color.updated_at,
                    product_id=color.product_id,
                )
                for color in colors
            ]