"""List products admin use case."""

from typing import Optional
from uuid import UUID

from app.application.dto.product_dto import ProductListResponse, ProductDTO
from app.application.interfaces.uow import UnitOfWork
from app.domain.entities.product import ProductStatus


class ListProductsAdminUseCase:
    """Use case for listing products (admin view with filters)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        category_id: Optional[UUID] = None,
        tag: Optional[str] = None,
        featured: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> ProductListResponse:
        """
        List products with pagination and filters (admin view).
        
        All products visible regardless of status.
        """
        async with self.uow:
            # Parse status
            product_status = ProductStatus(status) if status else None

            # Get products
            products, total = await self.uow.products.list_paginated(
                offset=offset,
                limit=limit,
                status=product_status,
                category_id=category_id,
                tag=tag,
                featured=featured,
                sort_by=sort_by,
                sort_desc=sort_desc,
            )

            # Convert to DTOs
            product_dtos = [
                ProductDTO(
                    id=p.id,
                    status=p.status.value,
                    name=p.name,
                    slug=str(p.slug),
                    description_short=p.description_short,
                    description_long=p.description_long,
                    tags=p.tags,
                    featured=p.featured,
                    sort_order=p.sort_order,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    created_by=p.created_by,
                    updated_by=p.updated_by,
                )
                for p in products
            ]

            return ProductListResponse(
                products=product_dtos,
                total=total,
                offset=offset,
                limit=limit,
            )
