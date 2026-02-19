"""Assign categories to product use case."""

from app.application.dto.product_dto import AssignCategoriesRequest
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.cache_port import CachePort


class AssignCategoriesUseCase:
    """Use case for assigning categories to a product."""

    def __init__(
        self,
        uow: UnitOfWork,
        audit_log: AuditLogPort,
        cache: CachePort,
    ) -> None:
        self.uow = uow
        self.audit_log = audit_log
        self.cache = cache

    async def execute(self, request: AssignCategoriesRequest) -> None:
        """
        Assign categories to product (replaces existing).
        
        Raises:
            ResourceNotFoundError: If product not found
        """
        async with self.uow:
            # Check product exists
            product = await self.uow.products.get_by_id(request.product_id)
            if not product:
                raise ResourceNotFoundError(f"Product {request.product_id} not found")

            # Verify all categories exist
            for category_id in request.category_ids:
                category = await self.uow.categories.get_by_id(category_id)
                if not category:
                    raise ResourceNotFoundError(f"Category {category_id} not found")

            # Assign categories
            await self.uow.products.assign_categories(request.product_id, request.category_ids)
            await self.uow.commit()

            # Invalidate cache
            await self.cache.delete(f"product:{request.product_id}")
            await self.cache.delete_pattern("products:storefront:*")

            # Audit log
            await self.audit_log.log_event(
                event_type="product.categories.assigned",
                user_id=None,
                details={
                    "product_id": str(request.product_id),
                    "category_ids": [str(cid) for cid in request.category_ids],
                },
            )
