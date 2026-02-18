"""Authentication routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.auth_dto import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
)
from app.application.dto.principal_dto import PrincipalDTO
from app.domain.errors.domain_errors import (
    InvalidCredentialsError,
    RefreshTokenExpiredError,
    RefreshTokenNotFoundError,
    RefreshTokenReuseDetectedError,
    RefreshTokenRevokedError,
    UserAlreadyExistsError,
    UserNotActiveError,
)
from app.infrastructure.db.sqlalchemy.session import get_session
from app.presentation.api.deps.auth_deps import get_current_principal, verify_csrf_token
from app.presentation.api.deps.container import Container, get_container
from app.presentation.api.schemas.http_auth_schemas import (
    ChangePasswordRequestSchema,
    LoginRequestSchema,
    LoginResponseSchema,
    MessageResponseSchema,
    PrincipalResponseSchema,
    RefreshResponseSchema,
    RegisterRequestSchema,
    RegisterResponseSchema,
)
from config.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponseSchema, status_code=status.HTTP_201_CREATED)
async def register(
    request_data: RegisterRequestSchema,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> RegisterResponseSchema:
    """Register a new user."""
    use_case = container.get_register_use_case(session)

    try:
        request = RegisterRequest(email=request_data.email, password=request_data.password)
        response = await use_case.execute(request)

        return RegisterResponseSchema(user_id=str(response.user_id), email=response.email)

    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=LoginResponseSchema)
async def login(
    request_data: LoginRequestSchema,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> LoginResponseSchema:
    """Login and obtain access token + refresh token cookie."""
    use_case = container.get_login_use_case(session)

    try:
        login_request = LoginRequest(
            email=request_data.email,
            password=request_data.password,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        login_response = await use_case.execute(login_request)

        # Set refresh token as HttpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=login_response.refresh_token,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
            path="/auth",
            max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        )

        # Set CSRF token cookie (NOT HttpOnly, so JS can read it)
        response.set_cookie(
            key="csrf_token",
            value=login_response.csrf_token,
            httponly=False,
            secure=settings.cookie_secure,
            samesite="lax",
            path="/",
            max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        )

        return LoginResponseSchema(
            access_token=login_response.access_token,
            token_type=login_response.token_type,
        )

    except (InvalidCredentialsError, UserNotActiveError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=RefreshResponseSchema, dependencies=[Depends(verify_csrf_token)])
async def refresh(
    request: Request,
    response: Response,
    refresh_token: str = Depends(lambda r: r.cookies.get("refresh_token")),
    csrf_token: str = Depends(lambda r: r.cookies.get("csrf_token")),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> RefreshResponseSchema:
    """Refresh access token using refresh token cookie."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    use_case = container.get_refresh_use_case(session)

    try:
        refresh_request = RefreshRequest(
            refresh_token=refresh_token,
            csrf_token=csrf_token,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        refresh_response = await use_case.execute(refresh_request)

        # Set new refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_response.refresh_token,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
            path="/auth",
            max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        )

        # Set new CSRF token cookie
        response.set_cookie(
            key="csrf_token",
            value=refresh_response.csrf_token,
            httponly=False,
            secure=settings.cookie_secure,
            samesite="lax",
            path="/",
            max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        )

        return RefreshResponseSchema(
            access_token=refresh_response.access_token,
            token_type=refresh_response.token_type,
        )

    except (
        RefreshTokenNotFoundError,
        RefreshTokenExpiredError,
        RefreshTokenRevokedError,
    ) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except RefreshTokenReuseDetectedError as e:
        # Clear cookies on reuse detection
        response.delete_cookie(key="refresh_token", path="/auth")
        response.delete_cookie(key="csrf_token", path="/")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", response_model=MessageResponseSchema, dependencies=[Depends(verify_csrf_token)])
async def logout(
    response: Response,
    refresh_token: str = Depends(lambda r: r.cookies.get("refresh_token")),
    csrf_token: str = Depends(lambda r: r.cookies.get("csrf_token")),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> MessageResponseSchema:
    """Logout by revoking current refresh token."""
    if not refresh_token:
        # Already logged out
        return MessageResponseSchema(message="Logged out successfully")

    use_case = container.get_logout_use_case(session)

    logout_request = LogoutRequest(refresh_token=refresh_token, csrf_token=csrf_token)
    await use_case.execute(logout_request)

    # Clear cookies
    response.delete_cookie(key="refresh_token", path="/auth")
    response.delete_cookie(key="csrf_token", path="/")

    return MessageResponseSchema(message="Logged out successfully")


@router.post("/logout-all", response_model=MessageResponseSchema, dependencies=[Depends(verify_csrf_token)])
async def logout_all(
    response: Response,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> MessageResponseSchema:
    """Logout all sessions by revoking all refresh tokens."""
    use_case = container.get_logout_all_use_case(session)
    await use_case.execute(principal.user_id)

    # Clear cookies
    response.delete_cookie(key="refresh_token", path="/auth")
    response.delete_cookie(key="csrf_token", path="/")

    return MessageResponseSchema(message="Logged out from all sessions")


@router.post("/change-password", response_model=MessageResponseSchema)
async def change_password(
    request_data: ChangePasswordRequestSchema,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> MessageResponseSchema:
    """Change user password."""
    use_case = container.get_change_password_use_case(session)

    try:
        change_request = ChangePasswordRequest(
            user_id=principal.user_id,
            old_password=request_data.old_password,
            new_password=request_data.new_password,
        )
        await use_case.execute(change_request)

        return MessageResponseSchema(message="Password changed successfully")

    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=PrincipalResponseSchema)
async def get_me(
    principal: PrincipalDTO = Depends(get_current_principal),
) -> PrincipalResponseSchema:
    """Get current user information."""
    return PrincipalResponseSchema(
        user_id=str(principal.user_id),
        email=principal.email,
        roles=principal.roles,
        is_active=principal.is_active,
    )
