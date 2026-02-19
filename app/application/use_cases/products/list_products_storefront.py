"""List products storefront use case."""

from typing import Optional
from uuid import UUID

from app.application.dto.product_dto import ProductListResponse, ProductDTO
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.cache_port import CachePort
from app.domain.entities.product import ProductStatus


class ListProductsStorefrontUseCase:
    """Use case for listing products (storefront - published only)."""

    def __init__(self, uow: UnitOfWork, cache: CachePort) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(
        self,
        offset: int = 0,
        limit: int = 20,
        category_id: Optional[UUID] = None,
        tag: Optional[str] = None,
        featured: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> ProductListResponse:
        """
        List published products with pagination and filters (storefront view).
        
        Only PUBLISHED products visible.
        """
        # Cache key
        cache_key = f"products:storefront:{offset}:{limit}:{category_id}:{tag}:{featured}:{sort_by}:{sort_desc}"
        cached = await self.cache.get(cache_key)
        if cached:
            pass  # Skip cache deserialization for now

        async with self.uow:
            # Get published products only
            products, total = await self.uow.products.list_paginated(
                offset=offset,
                limit=limit,
                status=ProductStatus.PUBLISHED,
                category_id=category_id,
                tag=tag,
                featured=featured,
                sort_by=sort_by,
                sort_desc=sort_desc,
            )

            # Convert to DTOs (limited fields for storefront)
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
                )
                for p in products
            ]

            response = ProductListResponse(
                products=product_dtos,
                total=total,
                offset=offset,
                limit=limit,
            )

            # Cache response (TTL 5 minutes)
            # await self.cache.set(cache_key, serialize(response), ttl=300)

            return response
