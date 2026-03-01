"""Customer order routes (authenticated) – checkout + order history."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.order_dto import (
    CheckoutRequest,
    GetMyOrdersRequest,
    GetOrderDetailRequest,
)
from app.application.errors.app_errors import (
    IdempotencyConflictError,
    OrderAccessDeniedError,
    ResourceNotFoundError,
    ValidationError,
)
from app.infrastructure.db.sqlalchemy.session import get_session
from app.presentation.api.deps.auth_deps import get_current_principal
from app.presentation.api.deps.container import Container, get_container
from app.presentation.api.routes.cart_routes import GUEST_TOKEN_COOKIE, get_optional_principal
from app.presentation.api.schemas.http_order_schemas import (
    CheckoutRequestSchema,
    OrderListResponseSchema,
    OrderResponseSchema,
    OrderItemResponseSchema,
)
from app.application.dto.principal_dto import PrincipalDTO

router = APIRouter(tags=["orders"])


def _build_order_response(dto) -> OrderResponseSchema:
    return OrderResponseSchema(
        id=dto.id,
        order_number=dto.order_number,
        status=dto.status,
        user_id=dto.user_id,
        subtotal_amount=dto.subtotal_amount,
        grand_total_amount=dto.grand_total_amount,
        currency=dto.currency,
        notes=dto.notes,
        shipping_address=dto.shipping_address,
        items=[
            OrderItemResponseSchema(
                id=i.id,
                variant_id=i.variant_id,
                product_name=i.product_name,
                variant_sku=i.variant_sku,
                variant_label=i.variant_label,
                unit_price_amount=i.unit_price_amount,
                unit_price_currency=i.unit_price_currency,
                quantity=i.quantity,
                line_total_amount=i.line_total_amount,
            )
            for i in dto.items
        ],
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


@router.post("/checkout", response_model=OrderResponseSchema, status_code=status.HTTP_201_CREATED)
async def checkout(
    request_data: CheckoutRequestSchema,
    request: Request,
    response: Response,
    idempotency_key: Annotated[Optional[str], Header(alias="Idempotency-Key")] = None,
    principal: Optional[PrincipalDTO] = Depends(get_optional_principal),
    cart_token: Annotated[Optional[str], Cookie(alias=GUEST_TOKEN_COOKIE)] = None,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> OrderResponseSchema:
    """
    Create an order from the current cart.

    Requires `Idempotency-Key` header (UUID or any opaque string).
    Authenticated users or guests with a cart_token cookie are supported.
    """
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required for checkout",
        )

    user_id = principal.user_id if principal else None
    guest_token = None if principal else cart_token

    if user_id is None and guest_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active session (login or provide cart_token cookie)",
        )

    use_case = container.get_checkout_use_case(session)
    try:
        order_dto = await use_case.execute(
            CheckoutRequest(
                idempotency_key=idempotency_key,
                user_id=user_id,
                guest_token=guest_token,
                shipping_address=request_data.shipping_address,
                notes=request_data.notes,
            )
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except IdempotencyConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return _build_order_response(order_dto)


@router.get("/orders", response_model=OrderListResponseSchema)
async def list_my_orders(
    offset: int = 0,
    limit: int = 20,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> OrderListResponseSchema:
    """List my orders (requires authentication)."""
    use_case = container.get_get_my_orders_use_case(session)
    result = await use_case.execute(
        GetMyOrdersRequest(user_id=principal.user_id, offset=offset, limit=limit)
    )
    return OrderListResponseSchema(
        orders=[_build_order_response(o) for o in result.orders],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.get("/orders/{order_id}", response_model=OrderResponseSchema)
async def get_my_order(
    order_id: UUID,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> OrderResponseSchema:
    """Get a single order (must belong to the authenticated user)."""
    use_case = container.get_get_order_detail_use_case(session)
    try:
        order_dto = await use_case.execute(
            GetOrderDetailRequest(order_id=order_id, user_id=principal.user_id)
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except OrderAccessDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return _build_order_response(order_dto)
