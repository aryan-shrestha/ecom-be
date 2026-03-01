"""Admin order management routes (RBAC protected)."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.order_dto import AdminCancelOrderRequest, AdminListOrdersRequest
from app.application.errors.app_errors import ResourceNotFoundError, ValidationError
from app.infrastructure.db.sqlalchemy.session import get_session
from app.presentation.api.deps.auth_deps import get_current_principal, require_permission
from app.presentation.api.deps.container import Container, get_container
from app.presentation.api.routes.order_routes import _build_order_response
from app.presentation.api.schemas.http_order_schemas import (
    OrderListResponseSchema,
    OrderResponseSchema,
)
from app.application.dto.principal_dto import PrincipalDTO

router = APIRouter(prefix="/admin/orders", tags=["admin-orders"])

_PERMISSION = "orders:manage"  # Register this permission in seed data


@router.get("", response_model=OrderListResponseSchema, dependencies=[Depends(require_permission(_PERMISSION))])
async def admin_list_orders(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    order_status: Optional[str] = Query(None, alias="status"),
    user_id: Optional[UUID] = None,
    order_number: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> OrderListResponseSchema:
    """Admin: list all orders with optional filters."""
    use_case = container.get_admin_list_orders_use_case(session)
    result = await use_case.execute(
        AdminListOrdersRequest(
            offset=offset,
            limit=limit,
            status=order_status,
            user_id=user_id,
            order_number=order_number,
            from_date=from_date,
            to_date=to_date,
        )
    )
    return OrderListResponseSchema(
        orders=[_build_order_response(o) for o in result.orders],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.get("/{order_id}", response_model=OrderResponseSchema, dependencies=[Depends(require_permission(_PERMISSION))])
async def admin_get_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> OrderResponseSchema:
    """Admin: retrieve any order by ID."""
    use_case = container.get_admin_get_order_use_case(session)
    try:
        order_dto = await use_case.execute(order_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _build_order_response(order_dto)


@router.post("/{order_id}/cancel", response_model=OrderResponseSchema, dependencies=[Depends(require_permission(_PERMISSION))])
async def admin_cancel_order(
    order_id: UUID,
    principal: PrincipalDTO = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> OrderResponseSchema:
    """Admin: cancel an order (only if not shipped/fulfilled)."""
    use_case = container.get_admin_cancel_order_use_case(session)
    try:
        order_dto = await use_case.execute(
            AdminCancelOrderRequest(order_id=order_id, canceled_by=principal.user_id)
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return _build_order_response(order_dto)
