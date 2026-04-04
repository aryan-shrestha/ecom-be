"""RBAC routes for role assignment."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.principal_dto import PrincipalDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.domain.errors.domain_errors import RoleNotFoundError, UserNotFoundError
from app.infrastructure.db.sqlalchemy.session import get_session
from app.presentation.api.deps.auth_deps import require_permission, get_current_principal
from app.presentation.api.deps.container import Container, get_container
from app.presentation.api.schemas.http_auth_schemas import (
    AssignRoleRequestSchema,
    MessageResponseSchema,
)
from app.presentation.api.schemas.http_role_schemas import AssignPermissionToRoleRequestSchema, RemovePermissionFromRoleRequestSchema, RoleCreateRequestSchema, RoleListResponseSchema, RoleResponseSchema
from app.presentation.api.schemas.http_permission_schemas import PermissionResponseSchema, PermissionListResponseSchema, PermissionCreateRequestSchema

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


@router.get(
    "/roles",
    response_model=RoleListResponseSchema,
    dependencies=[Depends(require_permission("roles:read"))],
)
async def list_roles(
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> RoleListResponseSchema:
    use_case = container.get_roles_list_use_case(session)
    roles_dto = await use_case.execute()

    return RoleListResponseSchema(
        roles=[
            RoleResponseSchema(
                id=str(role.id), 
                name=role.name
            ) for role in roles_dto.roles
        ]
    )


@router.get(
    "/roles/{role_name}",
    response_model=RoleResponseSchema,
    dependencies=[Depends(require_permission("roles:read"))],
)
async def get_role(
    role_name: str,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> RoleResponseSchema:
    use_case = container.get_role_detail_use_case(session)
    
    try:
        role_dto = await use_case.execute(role_name)
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return RoleResponseSchema(
        id=str(role_dto.id), 
        name=role_dto.name
    )


@router.post(
    "/roles",
    response_model=RoleResponseSchema,
    dependencies=[Depends(require_permission("roles:write"))],
)
async def create_role(
    role_data: RoleCreateRequestSchema,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> RoleResponseSchema:
    use_case = container.get_create_role_use_case(session)

    try:
        role_dto = await use_case.execute(role_data.name, user_id=principal.user_id) 
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return RoleResponseSchema(
        id=str(role_dto.id),
        name=role_dto.name
    )

@router.delete(
    "/roles/{role_name}",
    response_model=MessageResponseSchema,
    dependencies=[Depends(require_permission("roles:write"))],
)
async def delete_role(
    role_name: str,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> MessageResponseSchema:
    use_case = container.get_delete_role_use_case(session)

    try:
        await use_case.execute(role_name, user_id=principal.user_id)
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return MessageResponseSchema(
        message=f"Role '{role_name}' deleted successfully"
    )


@router.get(
    "/permissions",
    response_model=PermissionListResponseSchema,
    dependencies=[Depends(require_permission("permissions:read"))],
)
async def list_permissions(
    session: AsyncSession = Depends(get_session),
    principal: PrincipalDTO = Depends(get_current_principal),
    container: Container = Depends(get_container),
) -> PermissionListResponseSchema:
    use_case = container.get_list_permissions_use_case(session)
    permissions_dto = await use_case.execute()

    return PermissionListResponseSchema(
        permissions=[
            PermissionResponseSchema(
                id=str(permission.id), 
                code=permission.code
            ) for permission in permissions_dto.permissions
        ]
    )

@router.post(
    "/permissions",
    response_model=PermissionResponseSchema,
    dependencies=[Depends(require_permission("permissions:write"))],
)
async def create_permission(
    permission_data: PermissionCreateRequestSchema,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> PermissionResponseSchema:
    
    use_case = container.get_create_permission_use_case(session)

    try:
        permission_dto = await use_case.execute(permission_data.code, user_id=principal.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return PermissionResponseSchema(
        id=str(permission_dto.id),
        code=permission_dto.code
    )

@router.delete(
    "/permissions/{permission_code}",
    response_model=MessageResponseSchema,
    dependencies=[Depends(require_permission("permissions:write"))],
)
async def delete_permission(
    permission_code: str,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> MessageResponseSchema:
    use_case = container.get_delete_permission_use_case(session)

    try:
        await use_case.execute(permission_code, user_id=principal.user_id)
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return MessageResponseSchema(
        message=f"Permission '{permission_code}' deleted successfully"
    )


@router.get(
    "/roles/{role_name}/permissions",
    response_model=PermissionListResponseSchema,
    dependencies=[Depends(require_permission("roles:read"))],
)
async def get_permissions_for_role(
    role_name: str,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> PermissionListResponseSchema:
    
    use_case = container.get_permission_for_role_use_case(session)
    try:
        permissions_dto = await use_case.execute(role_name)
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return PermissionListResponseSchema(
        permissions=[
            PermissionResponseSchema(
                id=str(permission.id),
                code=permission.code
            ) for permission in permissions_dto
        ]
    )


@router.post(
    "/roles/{role_name}/assign-permission",
    response_model=MessageResponseSchema,
    dependencies=[Depends(require_permission("roles:write"))],
)
async def assign_permission_to_role(
    role_name: str,
    request_data: AssignPermissionToRoleRequestSchema,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> MessageResponseSchema:
    use_case = container.get_assign_permission_to_role_use_case(session)

    try:
        await use_case.execute(role_name, request_data.permission_code, user_id=principal.user_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return MessageResponseSchema(
        message=f"Permission '{request_data.permission_code}' assigned to role '{role_name}' successfully"
    )


@router.post(
    "/roles/{role_name}/remove-permission",
    response_model=MessageResponseSchema,
    dependencies=[Depends(require_permission("roles:write"))],
)
async def remove_permission_from_role(
    role_name: str,
    request_data: RemovePermissionFromRoleRequestSchema,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> MessageResponseSchema:
    use_case = container.get_remove_permission_from_role_use_case(session)

    try:
        await use_case.execute(role_name, request_data.permission_code, user_id=principal.user_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return MessageResponseSchema(
        message=f"Permission '{request_data.permission_code}' removed from role '{role_name}' successfully"
    )