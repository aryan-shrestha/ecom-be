"""Get single order detail use case (authenticated user, ownership enforced)."""

from app.application.dto.order_dto import GetOrderDetailRequest, OrderDTO, OrderItemDTO
from app.application.errors.app_errors import OrderAccessDeniedError, ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.use_cases.orders.get_my_orders import _to_dto


class GetOrderDetailUseCase:
    """Retrieve a single order, verifying the caller owns it."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, request: GetOrderDetailRequest) -> OrderDTO:
        async with self.uow:
            order = await self.uow.orders.get_by_id(request.order_id)
            if order is None:
                raise ResourceNotFoundError(f"Order {request.order_id} not found")
            if order.user_id != request.user_id:
                raise OrderAccessDeniedError("Access to this order is not allowed")
            return _to_dto(order)
