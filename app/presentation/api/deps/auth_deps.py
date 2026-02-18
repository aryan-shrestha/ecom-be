"""Authentication dependencies for FastAPI."""

import uuid
from typing import Annotated, Optional

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.principal_dto import PrincipalDTO
from app.application.use_cases.rbac.check_permission import CheckPermissionUseCase
from app.domain.entities.user import User
from app.infrastructure.db.sqlalchemy.session import get_session
from app.infrastructure.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from app.presentation.api.deps.container import Container, get_container


async def get_current_principal(
    request: Request,
    authorization: Annotated[Optional[str], Header()] = None,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> PrincipalDTO:
    """
    Get current authenticated principal from JWT.
    
    Verifies:
    - JWT signature and claims
    - User exists and is active
    - Token version matches user's current version
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "")

    try:
        # Verify JWT
        jwt_service = container.get_jwt_service()
        claims = jwt_service.verify_access_token(token)

        # Extract claims
        user_id = uuid.UUID(claims["sub"])
        roles = claims.get("roles", [])
        token_version = claims.get("ver", 0)

        # Load user from database
        uow = SqlAlchemyUnitOfWork(session)
        async with uow:
            user = await uow.users.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not active",
            )

        # Check token version
        if user.token_version != token_version:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )

        return PrincipalDTO(
            user_id=user.id,
            email=str(user.email),
            roles=roles,
            token_version=user.token_version,
            is_active=user.is_active,
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


def require_permission(permission_code: str):
    """
    Dependency factory for permission checking.
    
    Usage:
        @router.post("/admin", dependencies=[Depends(require_permission("admin:write"))])
    """

    async def permission_checker(
        principal: PrincipalDTO = Depends(get_current_principal),
        session: AsyncSession = Depends(get_session),
        container: Container = Depends(get_container),
    ) -> None:
        """Check if principal has required permission."""
        use_case = container.get_check_permission_use_case(session)

        try:
            await use_case.execute(principal.user_id, principal.roles, permission_code)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission_code}",
            )

    return permission_checker


def verify_csrf_token(
    x_csrf_token: Annotated[Optional[str], Header(alias="X-CSRF-Token")] = None,
    csrf_token: Annotated[Optional[str], Cookie()] = None,
) -> None:
    """
    Verify CSRF token for state-changing operations.
    
    Implements double-submit cookie pattern.
    """
    if not x_csrf_token or not csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing CSRF token",
        )

    if x_csrf_token != csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token mismatch",
        )
