"""Admin get order use case."""

from uuid import UUID

from app.application.dto.order_dto import OrderDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.use_cases.orders.get_my_orders import _to_dto


class AdminGetOrderUseCase:
    """Retrieve any order by ID (no ownership check – admin only)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, order_id: UUID) -> OrderDTO:
        async with self.uow:
            order = await self.uow.orders.get_by_id(order_id)
            if order is None:
                raise ResourceNotFoundError(f"Order {order_id} not found")
            return _to_dto(order)
