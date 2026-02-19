"""List categories use case."""

from app.application.dto.product_dto import CategoryDTO
from app.application.interfaces.uow import UnitOfWork


class ListCategoriesUseCase:
    """Use case for listing all categories."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self) -> list[CategoryDTO]:
        """List all categories."""
        async with self.uow:
            categories = await self.uow.categories.list_all()

            return [
                CategoryDTO(
                    id=cat.id,
                    name=cat.name,
                    slug=str(cat.slug),
                    parent_id=cat.parent_id,
                )
                for cat in categories
            ]
