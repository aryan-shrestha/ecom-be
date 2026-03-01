"""Get my orders use case (authenticated user)."""

from app.application.dto.order_dto import GetMyOrdersRequest, OrderDTO, OrderItemDTO, OrderListDTO
from app.application.interfaces.uow import UnitOfWork
from app.domain.entities.order import Order


def _to_dto(order: Order) -> OrderDTO:
    return OrderDTO(
        id=order.id,
        order_number=order.order_number,
        status=order.status.value,
        user_id=order.user_id,
        guest_token=order.guest_token,
        subtotal_amount=order.subtotal.amount,
        grand_total_amount=order.grand_total.amount,
        currency=order.currency,
        notes=order.notes,
        shipping_address=order.shipping_address,
        items=[
            OrderItemDTO(
                id=i.id,
                order_id=i.order_id,
                variant_id=i.variant_id,
                product_name=i.product_name,
                variant_sku=i.variant_sku,
                variant_label=i.variant_label,
                unit_price_amount=i.unit_price.amount,
                unit_price_currency=i.unit_price.currency,
                quantity=i.quantity,
                line_total_amount=i.line_total.amount,
            )
            for i in order.items
        ],
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


class GetMyOrdersUseCase:
    """List orders for the authenticated user."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, request: GetMyOrdersRequest) -> OrderListDTO:
        async with self.uow:
            orders, total = await self.uow.orders.list_for_user(
                user_id=request.user_id,
                offset=request.offset,
                limit=request.limit,
            )
            return OrderListDTO(
                orders=[_to_dto(o) for o in orders],
                total=total,
                offset=request.offset,
                limit=request.limit,
            )
