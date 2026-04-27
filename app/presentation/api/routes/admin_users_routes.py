"""Admin users routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.user_dto import UserDTO, UserListResponse
from app.application.dto.principal_dto import PrincipalDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.infrastructure.db.sqlalchemy.session import get_session
from app.presentation.api.deps.auth_deps import get_current_principal, require_permission
from app.presentation.api.deps.container import Container, get_container
from app.presentation.api.schemas.http_role_schemas import RoleListResponseSchema, RoleResponseSchema
from app.presentation.api.schemas.http_user_schemas import UserListResponseSchema, UserResponseSchema


router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


@router.get(
        "", 
        response_model=UserListResponseSchema, 
        dependencies=[Depends(require_permission("users:read"))]
    )
async def list_users(
    offset: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> UserListResponse:
    """List users with pagination - admin only."""

    use_case = container.get_user_list_admin_use_case(session)
    result = await use_case.execute(offset=offset, limit=limit)
    return UserListResponseSchema(
        users=[
            UserResponseSchema(
                id=u.id,
                email=str(u.email),
                first_name=u.first_name,
                last_name=u.last_name,
                is_active=u.is_active,
                is_verified=u.is_verified,
                created_at=u.created_at,
                updated_at=u.updated_at,
            ) for u in result.users
        ],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.get(
        "/{user_id}", 
        response_model=UserResponseSchema, 
        dependencies=[Depends(require_permission("users:read"))]
)
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> UserDTO:
    """Get user by ID - admin only."""
    use_case = container.get_user_detail_admin_use_case(session)
    user = await use_case.execute(user_id=user_id)
    if not user:
        raise ResourceNotFoundError("User not found")
    
    role_list_response_schema = RoleListResponseSchema(
        roles=[
            RoleResponseSchema(
                id=role.id,
                name=role.name
            ) for role in user.roles.roles
        ]
    ) if user.roles else None

    return UserResponseSchema(
        id=user.id,
        email=str(user.email),
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=role_list_response_schema
    )

@router.patch(
    "/{user_id}/deactivate",
    response_model=UserResponseSchema,
    dependencies=[Depends(require_permission("users:write"))]
)
async def deactivate_user(
    user_id: UUID,
    current_principal: Annotated[PrincipalDTO, Depends(get_current_principal)],
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> UserDTO:
    """Deactivate user by admin."""
    use_case = container.get_deactivate_user_admin_use_case(session)
    deactivated_user = await use_case.execute(user_id=user_id, deactivated_by=current_principal.user_id)

    return UserResponseSchema(
        id=deactivated_user.id,
        email=str(deactivated_user.email),
        first_name=deactivated_user.first_name,
        last_name=deactivated_user.last_name,
        is_active=deactivated_user.is_active,
        is_verified=deactivated_user.is_verified,
        created_at=deactivated_user.created_at,
        updated_at=deactivated_user.updated_at,
    )

