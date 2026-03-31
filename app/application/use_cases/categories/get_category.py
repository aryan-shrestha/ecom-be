from uuid import UUID

from app.application.dto.category_dto import CategoryDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork


class GetCategoryUseCase:
    """
    Use case for getting category details.
    """
    
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
    
    async def execute(self, category_id: UUID) -> CategoryDTO:
        """
        Get category details by ID.
        
        Raises:
            ResourceNotFoundError: If category not found
        """
        async with self.uow:
            category = await self.uow.categories.get_by_id(category_id)
            if not category:
                raise ResourceNotFoundError(f"Category {category_id} not found")
            
            return CategoryDTO(
                id=category.id,
                name=category.name,
                slug=str(category.slug),
                parent_id=category.parent_id,
            )