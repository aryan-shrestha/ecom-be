"""Admin product routes."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.product_dto import (
    CreateProductRequest,
    UpdateProductRequest,
    CreateVariantRequest,
    UpdateVariantRequest,
    AdjustStockRequest,
    AddProductImageRequest,
    ReorderImagesRequest,
    AssignCategoriesRequest,
)
from app.application.dto.principal_dto import PrincipalDTO
from app.application.errors.app_errors import (
    ConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.infrastructure.db.sqlalchemy.session import get_session
from app.presentation.api.deps.auth_deps import get_current_principal, require_permission
from app.presentation.api.deps.container import Container, get_container
from app.presentation.api.schemas.http_product_schemas import (
    CreateProductRequestSchema,
    UpdateProductRequestSchema,
    ProductResponseSchema,
    CreateVariantRequestSchema,
    UpdateVariantRequestSchema,
    VariantResponseSchema,
    AdjustStockRequestSchema,
    StockMovementResponseSchema,
    AddProductImageRequestSchema,
    ProductImageResponseSchema,
    ReorderImagesRequestSchema,
    AssignCategoriesRequestSchema,
    ProductDetailResponseSchema,
    ProductListResponseSchema,
    MoneySchema,
    InventoryResponseSchema,
    CategoryResponseSchema,
)
from app.presentation.api.schemas.http_auth_schemas import MessageResponseSchema

router = APIRouter(prefix="/admin/products", tags=["admin-products"])


@router.post(
    "",
    response_model=ProductResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("products:write"))],
)
async def create_product(
    request_data: CreateProductRequestSchema,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> ProductResponseSchema:
    """Create new product."""
    use_case = container.get_create_product_use_case(session)

    try:
        request = CreateProductRequest(
            name=request_data.name,
            slug=request_data.slug,
            description_short=request_data.description_short,
            description_long=request_data.description_long,
            tags=request_data.tags,
            featured=request_data.featured,
            sort_order=request_data.sort_order,
            created_by=principal.user_id,
        )
        result = await use_case.execute(request)

        return ProductResponseSchema(
            id=result.id,
            status=result.status,
            name=result.name,
            slug=result.slug,
            description_short=result.description_short,
            description_long=result.description_long,
            tags=result.tags,
            featured=result.featured,
            sort_order=result.sort_order,
            created_at=result.created_at,
            updated_at=result.updated_at,
            created_by=result.created_by,
            updated_by=result.updated_by,
        )
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=ProductListResponseSchema,
    dependencies=[Depends(require_permission("products:read"))],
)
async def list_products(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    category_id: Optional[UUID] = None,
    tag: Optional[str] = None,
    featured: Optional[bool] = None,
    sort_by: str = Query("created_at", regex="^(created_at|sort_order)$"),
    sort_desc: bool = True,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> ProductListResponseSchema:
    """List products with filters (admin view)."""
    use_case = container.get_list_products_admin_use_case(session)

    result = await use_case.execute(
        offset=offset,
        limit=limit,
        status=status,
        category_id=category_id,
        tag=tag,
        featured=featured,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    return ProductListResponseSchema(
        products=[
            ProductResponseSchema(
                id=p.id,
                status=p.status,
                name=p.name,
                slug=p.slug,
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
            for p in result.products
        ],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.get(
    "/{product_id}",
    response_model=ProductDetailResponseSchema,
    dependencies=[Depends(require_permission("products:read"))],
)
async def get_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> ProductDetailResponseSchema:
    """Get product detail (admin view)."""
    use_case = container.get_get_product_admin_use_case(session)

    try:
        result = await use_case.execute(product_id)

        return ProductDetailResponseSchema(
            product=ProductResponseSchema(
                id=result.product.id,
                status=result.product.status,
                name=result.product.name,
                slug=result.product.slug,
                description_short=result.product.description_short,
                description_long=result.product.description_long,
                tags=result.product.tags,
                featured=result.product.featured,
                sort_order=result.product.sort_order,
                created_at=result.product.created_at,
                updated_at=result.product.updated_at,
                created_by=result.product.created_by,
                updated_by=result.product.updated_by,
            ),
            variants=[
                VariantResponseSchema(
                    id=v.id,
                    product_id=v.product_id,
                    sku=v.sku,
                    barcode=v.barcode,
                    status=v.status,
                    price=MoneySchema(amount=v.price.amount, currency=v.price.currency),
                    compare_at_price=(
                        MoneySchema(amount=v.compare_at_price.amount, currency=v.compare_at_price.currency)
                        if v.compare_at_price
                        else None
                    ),
                    cost=(
                        MoneySchema(amount=v.cost.amount, currency=v.cost.currency) if v.cost else None
                    ),
                    weight=v.weight,
                    length=v.length,
                    width=v.width,
                    height=v.height,
                    is_default=v.is_default,
                    created_at=v.created_at,
                    updated_at=v.updated_at,
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
            inventory={
                vid: InventoryResponseSchema(
                    variant_id=inv.variant_id,
                    on_hand=inv.on_hand,
                    reserved=inv.reserved,
                    allow_backorder=inv.allow_backorder,
                    available=inv.on_hand - inv.reserved,
                )
                for vid, inv in result.inventory_map.items()
            },
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{product_id}",
    response_model=ProductResponseSchema,
    dependencies=[Depends(require_permission("products:write"))],
)
async def update_product(
    product_id: UUID,
    request_data: UpdateProductRequestSchema,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> ProductResponseSchema:
    """Update product."""
    use_case = container.get_update_product_use_case(session)

    try:
        request = UpdateProductRequest(
            product_id=product_id,
            name=request_data.name,
            description_short=request_data.description_short,
            description_long=request_data.description_long,
            tags=request_data.tags,
            featured=request_data.featured,
            sort_order=request_data.sort_order,
            updated_by=principal.user_id,
        )
        result = await use_case.execute(request)

        return ProductResponseSchema(
            id=result.id,
            status=result.status,
            name=result.name,
            slug=result.slug,
            description_short=result.description_short,
            description_long=result.description_long,
            tags=result.tags,
            featured=result.featured,
            sort_order=result.sort_order,
            created_at=result.created_at,
            updated_at=result.updated_at,
            created_by=result.created_by,
            updated_by=result.updated_by,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{product_id}/publish",
    response_model=ProductResponseSchema,
    dependencies=[Depends(require_permission("products:publish"))],
)
async def publish_product(
    product_id: UUID,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> ProductResponseSchema:
    """Publish product."""
    use_case = container.get_publish_product_use_case(session)

    try:
        result = await use_case.execute(product_id, principal.user_id)

        return ProductResponseSchema(
            id=result.id,
            status=result.status,
            name=result.name,
            slug=result.slug,
            description_short=result.description_short,
            description_long=result.description_long,
            tags=result.tags,
            featured=result.featured,
            sort_order=result.sort_order,
            created_at=result.created_at,
            updated_at=result.updated_at,
            created_by=result.created_by,
            updated_by=result.updated_by,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{product_id}/archive",
    response_model=ProductResponseSchema,
    dependencies=[Depends(require_permission("products:archive"))],
)
async def archive_product(
    product_id: UUID,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> ProductResponseSchema:
    """Archive product."""
    use_case = container.get_archive_product_use_case(session)

    try:
        result = await use_case.execute(product_id, principal.user_id)

        return ProductResponseSchema(
            id=result.id,
            status=result.status,
            name=result.name,
            slug=result.slug,
            description_short=result.description_short,
            description_long=result.description_long,
            tags=result.tags,
            featured=result.featured,
            sort_order=result.sort_order,
            created_at=result.created_at,
            updated_at=result.updated_at,
            created_by=result.created_by,
            updated_by=result.updated_by,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Variant endpoints


@router.post(
    "/{product_id}/variants",
    response_model=VariantResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("products:variant_write"))],
)
async def add_variant(
    product_id: UUID,
    request_data: CreateVariantRequestSchema,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> VariantResponseSchema:
    """Add variant to product."""
    use_case = container.get_add_variant_use_case(session)

    try:
        request = CreateVariantRequest(
            product_id=product_id,
            sku=request_data.sku,
            barcode=request_data.barcode,
            price_amount=request_data.price_amount,
            price_currency=request_data.price_currency,
            compare_at_price_amount=request_data.compare_at_price_amount,
            compare_at_price_currency=request_data.compare_at_price_currency,
            cost_amount=request_data.cost_amount,
            cost_currency=request_data.cost_currency,
            weight=request_data.weight,
            length=request_data.length,
            width=request_data.width,
            height=request_data.height,
            is_default=request_data.is_default,
            initial_stock=request_data.initial_stock,
            allow_backorder=request_data.allow_backorder,
        )
        result = await use_case.execute(request)

        return VariantResponseSchema(
            id=result.id,
            product_id=result.product_id,
            sku=result.sku,
            barcode=result.barcode,
            status=result.status,
            price=MoneySchema(amount=result.price.amount, currency=result.price.currency),
            compare_at_price=(
                MoneySchema(amount=result.compare_at_price.amount, currency=result.compare_at_price.currency)
                if result.compare_at_price
                else None
            ),
            cost=MoneySchema(amount=result.cost.amount, currency=result.cost.currency) if result.cost else None,
            weight=result.weight,
            length=result.length,
            width=result.width,
            height=result.height,
            is_default=result.is_default,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
    except (ResourceNotFoundError, ConflictError) as e:
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=status_code, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/variants/{variant_id}",
    response_model=VariantResponseSchema,
    dependencies=[Depends(require_permission("products:variant_write"))],
)
async def update_variant(
    variant_id: UUID,
    request_data: UpdateVariantRequestSchema,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> VariantResponseSchema:
    """Update variant."""
    use_case = container.get_update_variant_use_case(session)

    try:
        request = UpdateVariantRequest(
            variant_id=variant_id,
            barcode=request_data.barcode,
            status=request_data.status,
            price_amount=request_data.price_amount,
            price_currency=request_data.price_currency,
            compare_at_price_amount=request_data.compare_at_price_amount,
            compare_at_price_currency=request_data.compare_at_price_currency,
            cost_amount=request_data.cost_amount,
            cost_currency=request_data.cost_currency,
            weight=request_data.weight,
            length=request_data.length,
            width=request_data.width,
            height=request_data.height,
        )
        result = await use_case.execute(request)

        return VariantResponseSchema(
            id=result.id,
            product_id=result.product_id,
            sku=result.sku,
            barcode=result.barcode,
            status=result.status,
            price=MoneySchema(amount=result.price.amount, currency=result.price.currency),
            compare_at_price=(
                MoneySchema(amount=result.compare_at_price.amount, currency=result.compare_at_price.currency)
                if result.compare_at_price
                else None
            ),
            cost=MoneySchema(amount=result.cost.amount, currency=result.cost.currency) if result.cost else None,
            weight=result.weight,
            length=result.length,
            width=result.width,
            height=result.height,
            is_default=result.is_default,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/variants/{variant_id}/deactivate",
    response_model=VariantResponseSchema,
    dependencies=[Depends(require_permission("products:variant_write"))],
)
async def deactivate_variant(
    variant_id: UUID,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> VariantResponseSchema:
    """Deactivate variant."""
    use_case = container.get_deactivate_variant_use_case(session)

    try:
        result = await use_case.execute(variant_id, principal.user_id)

        return VariantResponseSchema(
            id=result.id,
            product_id=result.product_id,
            sku=result.sku,
            barcode=result.barcode,
            status=result.status,
            price=MoneySchema(amount=result.price.amount, currency=result.price.currency),
            compare_at_price=(
                MoneySchema(amount=result.compare_at_price.amount, currency=result.compare_at_price.currency)
                if result.compare_at_price
                else None
            ),
            cost=MoneySchema(amount=result.cost.amount, currency=result.cost.currency) if result.cost else None,
            weight=result.weight,
            length=result.length,
            width=result.width,
            height=result.height,
            is_default=result.is_default,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Stock adjustment endpoint


@router.post(
    "/variants/{variant_id}/stock-adjustments",
    response_model=StockMovementResponseSchema,
    dependencies=[Depends(require_permission("inventory:adjust"))],
)
async def adjust_stock(
    variant_id: UUID,
    request_data: AdjustStockRequestSchema,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> StockMovementResponseSchema:
    """Adjust variant stock."""
    use_case = container.get_adjust_stock_use_case(session)

    try:
        request = AdjustStockRequest(
            variant_id=variant_id,
            delta=request_data.delta,
            reason=request_data.reason,
            note=request_data.note,
            created_by=principal.user_id,
        )
        result = await use_case.execute(request)

        return StockMovementResponseSchema(
            id=result.id,
            variant_id=result.variant_id,
            delta=result.delta,
            reason=result.reason,
            note=result.note,
            created_at=result.created_at,
            created_by=result.created_by,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Image endpoints


@router.post(
    "/{product_id}/images",
    response_model=ProductImageResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("products:media_write"))],
)
async def add_product_image(
    product_id: UUID,
    request_data: AddProductImageRequestSchema,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> ProductImageResponseSchema:
    """Add image to product."""
    use_case = container.get_add_product_image_use_case(session)

    try:
        request = AddProductImageRequest(
            product_id=product_id,
            url=request_data.url,
            alt_text=request_data.alt_text,
        )
        result = await use_case.execute(request)

        return ProductImageResponseSchema(
            id=result.id,
            product_id=result.product_id,
            url=result.url,
            alt_text=result.alt_text,
            position=result.position,
            created_at=result.created_at,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{product_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("products:media_write"))],
)
async def remove_product_image(
    product_id: UUID,
    image_id: UUID,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> None:
    """Remove image from product."""
    use_case = container.get_remove_product_image_use_case(session)

    try:
        await use_case.execute(product_id, image_id, principal.user_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{product_id}/images/reorder",
    response_model=MessageResponseSchema,
    dependencies=[Depends(require_permission("products:media_write"))],
)
async def reorder_images(
    product_id: UUID,
    request_data: ReorderImagesRequestSchema,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> MessageResponseSchema:
    """Reorder product images."""
    use_case = container.get_reorder_product_images_use_case(session)

    try:
        request = ReorderImagesRequest(
            product_id=product_id,
            image_positions=request_data.image_positions,
        )
        await use_case.execute(request)

        return MessageResponseSchema(message="Images reordered successfully")
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Category assignment endpoint


@router.post(
    "/{product_id}/categories",
    response_model=MessageResponseSchema,
    dependencies=[Depends(require_permission("categories:write"))],
)
async def assign_categories(
    product_id: UUID,
    request_data: AssignCategoriesRequestSchema,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> MessageResponseSchema:
    """Assign categories to product."""
    use_case = container.get_assign_categories_use_case(session)

    try:
        request = AssignCategoriesRequest(
            product_id=product_id,
            category_ids=request_data.category_ids,
        )
        await use_case.execute(request)

        return MessageResponseSchema(message="Categories assigned successfully")
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
