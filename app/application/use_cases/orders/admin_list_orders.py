"""Admin list orders use case."""

from app.application.dto.order_dto import AdminListOrdersRequest, OrderDTO, OrderListDTO
from app.application.interfaces.uow import UnitOfWork
from app.application.use_cases.orders.get_my_orders import _to_dto
from app.domain.entities.order import OrderStatus


class AdminListOrdersUseCase:
    """List all orders with optional filters (admin only)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, request: AdminListOrdersRequest) -> OrderListDTO:
        status = None
        if request.status:
            try:
                status = OrderStatus(request.status)
            except ValueError:
                status = None

        async with self.uow:
            orders, total = await self.uow.orders.list_admin(
                offset=request.offset,
                limit=request.limit,
                status=status,
                user_id=request.user_id,
                order_number=request.order_number,
                from_date=request.from_date,
                to_date=request.to_date,
            )
            return OrderListDTO(
                orders=[_to_dto(o) for o in orders],
                total=total,
                offset=request.offset,
                limit=request.limit,
            )
