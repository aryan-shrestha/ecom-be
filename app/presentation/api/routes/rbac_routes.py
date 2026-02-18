"""RBAC routes for role assignment."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.errors.domain_errors import RoleNotFoundError, UserNotFoundError
from app.infrastructure.db.sqlalchemy.session import get_session
from app.presentation.api.deps.auth_deps import require_permission
from app.presentation.api.deps.container import Container, get_container
from app.presentation.api.schemas.http_auth_schemas import (
    AssignRoleRequestSchema,
    MessageResponseSchema,
)

router = APIRouter(prefix="/rbac", tags=["rbac"])


@router.post(
    "/assign-role",
    response_model=MessageResponseSchema,
    dependencies=[Depends(require_permission("rbac:assign"))],
)
async def assign_role(
    request_data: AssignRoleRequestSchema,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> MessageResponseSchema:
    """Assign role to user (requires 'rbac:assign' permission)."""
    use_case = container.get_assign_role_use_case(session)

    try:
        user_id = uuid.UUID(request_data.user_id)
        await use_case.execute(user_id, request_data.role_name)

        return MessageResponseSchema(
            message=f"Role '{request_data.role_name}' assigned to user {request_data.user_id}"
        )

    except (UserNotFoundError, RoleNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")
