import uuid
from app.application.dto.size_dto import SizeDTO
from app.application.interfaces.uow import UnitOfWork
from app.application.errors.app_errors import ResourceNotFoundError


class ListSizeByProductUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow
    
    async def execute(self, product_id: uuid.UUID) -> list[SizeDTO]:
        """
        List sizes by product.

        Raises:
            ResourceNotFoundError: If product not found
        """
        async with self.uow:
            # Check product exists
            product = await self.uow.products.get_by_id(product_id)
            if not product:
                raise ResourceNotFoundError(f"Product {product_id} not found")

            sizes = await self.uow.sizes.list_by_product_id(product_id)

            return [
                SizeDTO(
                    id=size.id,
                    product_id=size.product_id,
                    name=size.name,
                    created_at=size.created_at,
                    updated_at=size.updated_at,
                )
                for size in sizes
            ]