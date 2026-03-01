"""Cart routes (storefront) – supports both guests and authenticated users."""

import secrets
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.cart_dto import (
    AddCartItemRequest,
    ClearCartRequest,
    GetCartRequest,
    RemoveCartItemRequest,
    UpdateCartItemRequest,
)
from app.application.dto.principal_dto import PrincipalDTO
from app.application.errors.app_errors import ResourceNotFoundError, ValidationError
from app.infrastructure.db.sqlalchemy.session import get_session
from app.presentation.api.deps.container import Container, get_container
from app.presentation.api.schemas.http_cart_schemas import (
    AddCartItemRequestSchema,
    CartResponseSchema,
    CartItemResponseSchema,
    UpdateCartItemRequestSchema,
)
from config.settings import settings

router = APIRouter(prefix="/cart", tags=["cart"])

GUEST_TOKEN_COOKIE = "cart_token"
GUEST_TOKEN_TTL = 90 * 24 * 60 * 60  # 90 days


# ---------------------------------------------------------------------------
# Helper: optional JWT principal (does NOT raise on missing auth)
# ---------------------------------------------------------------------------

async def get_optional_principal(
    authorization: Annotated[Optional[str], Header()] = None,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> Optional[PrincipalDTO]:
    """Return PrincipalDTO if a valid Bearer token is provided, else None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    from app.presentation.api.deps.auth_deps import get_current_principal
    from fastapi import Request as _Request

    try:
        import jwt as _jwt  # noqa: F401
        jwt_service = container.get_jwt_service()
        token = authorization.replace("Bearer ", "")
        claims = jwt_service.verify_access_token(token)
        import uuid as _uuid
        user_id = _uuid.UUID(claims["sub"])
        roles = claims.get("roles", [])
        token_version = claims.get("ver", 0)

        from app.infrastructure.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
        uow = SqlAlchemyUnitOfWork(session)
        async with uow:
            user = await uow.users.get_by_id(user_id)

        if not user or not user.is_active or user.token_version != token_version:
            return None

        return PrincipalDTO(
            user_id=user.id,
            email=str(user.email),
            roles=roles,
            token_version=user.token_version,
            is_active=user.is_active,
        )
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Helper: extract actor info from request
# ---------------------------------------------------------------------------

def _resolve_actor(
    principal: Optional[PrincipalDTO],
    cart_token: Optional[str],
) -> tuple[Optional[UUID], Optional[str]]:
    """Return (user_id, guest_token) – exactly one will be set."""
    if principal is not None:
        return principal.user_id, None
    return None, cart_token or None


def _set_guest_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=GUEST_TOKEN_COOKIE,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=GUEST_TOKEN_TTL,
        path="/",
    )


def _build_cart_response(dto) -> CartResponseSchema:
    return CartResponseSchema(
        id=dto.id,
        status=dto.status,
        user_id=dto.user_id,
        items=[
            CartItemResponseSchema(
                id=i.id,
                cart_id=i.cart_id,
                variant_id=i.variant_id,
                quantity=i.quantity,
                unit_price_amount=i.unit_price_amount,
                unit_price_currency=i.unit_price_currency,
                line_subtotal_amount=i.line_subtotal_amount,
            )
            for i in dto.items
        ],
        subtotal_amount=dto.subtotal_amount,
        subtotal_currency=dto.subtotal_currency,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=CartResponseSchema)
async def get_cart(
    response: Response,
    principal: Optional[PrincipalDTO] = Depends(get_optional_principal),
    cart_token: Annotated[Optional[str], Cookie()] = None,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> CartResponseSchema:
    """Get current cart. Creates one if none exists."""
    user_id, guest_token = _resolve_actor(principal, cart_token)

    # Create new guest token if needed
    if user_id is None and guest_token is None:
        guest_token = secrets.token_urlsafe(32)
        _set_guest_cookie(response, guest_token)

    use_case = container.get_get_cart_use_case(session)
    cart_dto = await use_case.execute(GetCartRequest(user_id=user_id, guest_token=guest_token))

    if user_id is None and guest_token:
        _set_guest_cookie(response, guest_token)

    return _build_cart_response(cart_dto)


@router.post("/items", response_model=CartResponseSchema, status_code=status.HTTP_201_CREATED)
async def add_cart_item(
    request_data: AddCartItemRequestSchema,
    response: Response,
    principal: Optional[PrincipalDTO] = Depends(get_optional_principal),
    cart_token: Annotated[Optional[str], Cookie()] = None,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> CartResponseSchema:
    """Add a variant to the cart."""
    user_id, guest_token = _resolve_actor(principal, cart_token)

    if user_id is None and guest_token is None:
        guest_token = secrets.token_urlsafe(32)
        _set_guest_cookie(response, guest_token)

    use_case = container.get_add_cart_item_use_case(session)
    try:
        cart_dto = await use_case.execute(
            AddCartItemRequest(
                variant_id=request_data.variant_id,
                quantity=request_data.quantity,
                user_id=user_id,
                guest_token=guest_token,
            )
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    if user_id is None and guest_token:
        _set_guest_cookie(response, guest_token)

    return _build_cart_response(cart_dto)


@router.patch("/items/{item_id}", response_model=CartResponseSchema)
async def update_cart_item(
    item_id: UUID,
    request_data: UpdateCartItemRequestSchema,
    response: Response,
    principal: Optional[PrincipalDTO] = Depends(get_optional_principal),
    cart_token: Annotated[Optional[str], Cookie()] = None,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> CartResponseSchema:
    """Update the quantity of a cart item."""
    user_id, guest_token = _resolve_actor(principal, cart_token)

    use_case = container.get_update_cart_item_use_case(session)
    try:
        cart_dto = await use_case.execute(
            UpdateCartItemRequest(
                item_id=item_id,
                quantity=request_data.quantity,
                user_id=user_id,
                guest_token=guest_token,
            )
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return _build_cart_response(cart_dto)


@router.delete("/items/{item_id}", response_model=CartResponseSchema)
async def remove_cart_item(
    item_id: UUID,
    response: Response,
    principal: Optional[PrincipalDTO] = Depends(get_optional_principal),
    cart_token: Annotated[Optional[str], Cookie()] = None,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> CartResponseSchema:
    """Remove a single item from the cart."""
    user_id, guest_token = _resolve_actor(principal, cart_token)

    use_case = container.get_remove_cart_item_use_case(session)
    try:
        cart_dto = await use_case.execute(
            RemoveCartItemRequest(item_id=item_id, user_id=user_id, guest_token=guest_token)
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return _build_cart_response(cart_dto)


@router.post("/clear", response_model=CartResponseSchema)
async def clear_cart(
    response: Response,
    principal: Optional[PrincipalDTO] = Depends(get_optional_principal),
    cart_token: Annotated[Optional[str], Cookie()] = None,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> CartResponseSchema:
    """Remove all items from the cart."""
    user_id, guest_token = _resolve_actor(principal, cart_token)

    use_case = container.get_clear_cart_use_case(session)
    try:
        cart_dto = await use_case.execute(
            ClearCartRequest(user_id=user_id, guest_token=guest_token)
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return _build_cart_response(cart_dto)
