"""Storefront product routes (public, published products only)."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.errors.app_errors import ResourceNotFoundError
from app.infrastructure.db.sqlalchemy.session import get_session
from app.presentation.api.deps.container import Container, get_container
from app.presentation.api.schemas.http_product_schemas import (
    StorefrontProductDetailResponseSchema,
    StorefrontProductListResponseSchema,
    StorefrontProductListItemSchema,
    StorefrontVariantResponseSchema,
    ProductImageResponseSchema,
    CategoryResponseSchema,
    MoneySchema,
)

router = APIRouter(prefix="/store/products", tags=["storefront"])


@router.get("", response_model=StorefrontProductListResponseSchema)
async def list_published_products(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[UUID] = None,
    tag: Optional[str] = None,
    featured: Optional[bool] = None,
    sort_by: str = Query("created_at", regex="^(created_at|sort_order)$"),
    sort_desc: bool = True,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> StorefrontProductListResponseSchema:
    """List published products (storefront view)."""
    use_case = container.get_list_products_storefront_use_case(session)

    result = await use_case.execute(
        offset=offset,
        limit=limit,
        category_id=category_id,
        tag=tag,
        featured=featured,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    return StorefrontProductListResponseSchema(
        products=[
            StorefrontProductListItemSchema(
                id=p.id,
                slug=p.slug,
                name=p.name,
                description_short=p.description_short,
                tags=p.tags,
                featured=p.featured,
            )
            for p in result.products
        ],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.get("/{slug}", response_model=StorefrontProductDetailResponseSchema)
async def get_published_product(
    slug: str,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> StorefrontProductDetailResponseSchema:
    """Get published product by slug (storefront view)."""
    use_case = container.get_get_product_storefront_use_case(session)

    try:
        result = await use_case.execute(slug)

        return StorefrontProductDetailResponseSchema(
            id=result.product.id,
            slug=result.product.slug,
            name=result.product.name,
            description_short=result.product.description_short,
            description_long=result.product.description_long,
            tags=result.product.tags,
            featured=result.product.featured,
            variants=[
                StorefrontVariantResponseSchema(
                    id=v.id,
                    sku=v.sku,
                    price=MoneySchema(amount=v.price.amount, currency=v.price.currency),
                    compare_at_price=(
                        MoneySchema(amount=v.compare_at_price.amount, currency=v.compare_at_price.currency)
                        if v.compare_at_price
                        else None
                    ),
                    is_default=v.is_default,
                    in_stock=(
                        result.inventory_map[v.id].on_hand - result.inventory_map[v.id].reserved > 0
                        or result.inventory_map[v.id].allow_backorder
                    )
                    if v.id in result.inventory_map
                    else False,
                )
                for v in result.variants
            ],
            images=[
                ProductImageResponseSchema(
                    id=img.id,
                    product_id=img.product_id,
                    url=img.url,
                    alt_text=img.alt_text,
                    position=img.position,
                    created_at=img.created_at,
                )
                for img in result.images
            ],
            categories=[
                CategoryResponseSchema(
                    id=cat.id,
                    name=cat.name,
                    slug=cat.slug,
                    parent_id=cat.parent_id,
                )
                for cat in result.categories
            ],
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
