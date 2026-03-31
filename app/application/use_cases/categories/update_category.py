"""Update category use case"""

from app.application.dto.category_dto import CategoryDTO, UpdateCategoryRequest
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.domain.entities.category import Category
from app.domain.value_objects.slug import Slug



class UpdateCategoryUseCase:
    """Use case for updating an existing product."""
    
    def __init__(
        self,
        uow: UnitOfWork,
        audit_log: AuditLogPort,
    ) -> None:
        self.uow = uow
        self.audit_log = audit_log
   
    
    async def execute(self, request: UpdateCategoryRequest) -> CategoryDTO:
        """
        Update category details.
        
        Raises:
            ResourceNotFoundError: If category not found
        """
        async with self.uow:
            category = await self.uow.categories.get_by_id(request.id)
            if not category:
                raise ResourceNotFoundError(f"Category {request.id} not found")
            slug = Slug.from_string_and_id(request.name, request.id)
         
            updated_category =  category.update(
                name=request.name,
                parent_id=request.parent_id,
                slug=slug,
            )

            category = await self.uow.categories.update(updated_category)
            await self.uow.commit()

            await self.audit_log.log_event(
                event_type="category.updated",
                user_id=request.updated_by,
                details={
                    "category_id": str(category.id),
                    "name": category.name,
                    "slug": str(category.slug),
                },
            )
            
            return CategoryDTO(
                id=category.id,
                name=category.name,
                slug=str(category.slug),
                parent_id=category.parent_id,
            )
        