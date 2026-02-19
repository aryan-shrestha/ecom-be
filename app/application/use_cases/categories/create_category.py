"""Create category use case."""

import uuid

from app.application.dto.product_dto import CreateCategoryRequest, CategoryDTO
from app.application.errors.app_errors import ConflictError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.domain.entities.category import Category
from app.domain.value_objects.slug import Slug


class CreateCategoryUseCase:
    """Use case for creating a category."""

    def __init__(self, uow: UnitOfWork, audit_log: AuditLogPort) -> None:
        self.uow = uow
        self.audit_log = audit_log

    async def execute(self, request: CreateCategoryRequest) -> CategoryDTO:
        """
        Create new category.
        
        Raises:
            ConflictError: If category with slug already exists
        """
        slug = Slug.from_string(request.slug)

        async with self.uow:
            # Check slug uniqueness
            if await self.uow.categories.exists_by_slug(slug):
                raise ConflictError(f"Category with slug '{slug}' already exists")

            # Create category
            category = Category(
                id=uuid.uuid4(),
                name=request.name,
                slug=slug,
                parent_id=request.parent_id,
            )

            # Save
            category = await self.uow.categories.save(category)
            await self.uow.commit()

            # Audit log
            await self.audit_log.log_event(
                event_type="category.created",
                user_id=None,
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
