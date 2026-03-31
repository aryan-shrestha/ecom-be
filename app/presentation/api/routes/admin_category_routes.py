"""Admin category routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.principal_dto import PrincipalDTO
from app.application.dto.category_dto import CreateCategoryRequest, UpdateCategoryRequest
from app.application.errors.app_errors import ConflictError, ResourceNotFoundError
from app.infrastructure.db.sqlalchemy.session import get_session
from app.presentation.api.deps.auth_deps import get_current_principal, require_permission
from app.presentation.api.deps.container import Container, get_container
from app.presentation.api.schemas.http_category_schemas import (
    CreateCategoryRequestSchema,
    UpdateCategoryRequestSchema,
    CategoryResponseSchema,
)

router = APIRouter(prefix="/admin/categories", tags=["admin-categories"])


@router.post(
    "",
    response_model=CategoryResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("categories:write"))],
)
async def create_category(
    request_data: CreateCategoryRequestSchema,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> CategoryResponseSchema:
    """Create new category."""
    use_case = container.get_create_category_use_case(session)

    try:
        request = CreateCategoryRequest(
            name=request_data.name,
            parent_id=request_data.parent_id,
        )
        result = await use_case.execute(request)

        return CategoryResponseSchema(
            id=result.id,
            name=result.name,
            slug=result.slug,
            parent_id=result.parent_id,
        )
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=list[CategoryResponseSchema],
    dependencies=[Depends(require_permission("categories:read"))],
)
async def list_categories(
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> list[CategoryResponseSchema]:
    """List all categories."""
    use_case = container.get_list_categories_use_case(session)

    result = await use_case.execute()

    return [
        CategoryResponseSchema(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            parent_id=cat.parent_id,
        )
        for cat in result
    ]


@router.get(
    "/{category_id}",
    response_model=CategoryResponseSchema,
    dependencies=[Depends(require_permission("categories:read"))],
)
async def get_category(
    category_id: UUID,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> CategoryResponseSchema:
    """Get category details."""
    use_case = container.get_get_category_use_case(session)

    try:
        result = await use_case.execute(category_id)

        return CategoryResponseSchema(
            id=result.id,
            name=result.name,
            slug=result.slug,
            parent_id=result.parent_id,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{category_id}",
    response_model=CategoryResponseSchema,
    dependencies=[Depends(require_permission("categories:write"))],
)
async def update_category(
    category_id: UUID,
    request_data: UpdateCategoryRequestSchema,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> CategoryResponseSchema:
    """Update existing category."""
    use_case = container.get_update_category_use_case(session)

    try:
        request = UpdateCategoryRequest(
            id=category_id,
            name=request_data.name,
            parent_id=request_data.parent_id,
            updated_by=principal.user_id,
        )
        result = await use_case.execute(request)

        return CategoryResponseSchema(
            id=result.id,
            name=result.name,
            slug=result.slug,
            parent_id=result.parent_id,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))