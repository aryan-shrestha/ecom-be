"""Admin cancel order use case."""

from app.application.dto.order_dto import AdminCancelOrderRequest, OrderDTO
from app.application.errors.app_errors import ResourceNotFoundError, ValidationError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.application.use_cases.orders.get_my_orders import _to_dto
from app.domain.errors.domain_errors import (
    OrderAlreadyCanceledError,
    OrderCancelForbiddenError,
)
from app.domain.policies.order_policy import OrderPolicy


class AdminCancelOrderUseCase:
    """Cancel an order (admin only). Releases reserved inventory."""

    def __init__(self, uow: UnitOfWork, clock: ClockPort, audit_log: AuditLogPort) -> None:
        self.uow = uow
        self.clock = clock
        self.audit_log = audit_log

    async def execute(self, request: AdminCancelOrderRequest) -> OrderDTO:
        async with self.uow:
            order = await self.uow.orders.get_by_id(request.order_id)
            if order is None:
                raise ResourceNotFoundError(f"Order {request.order_id} not found")

            try:
                OrderPolicy.validate_can_cancel(order)
            except (OrderAlreadyCanceledError, OrderCancelForbiddenError) as e:
                raise ValidationError(str(e))

            now = self.clock.now()

            # Release reserved inventory for each item
            for item in order.items:
                inventory = await self.uow.inventory.get_by_variant_id_for_update(item.variant_id)
                if inventory is not None and inventory.reserved >= item.quantity:
                    released = inventory.release(item.quantity)
                    await self.uow.inventory.update(released)

            canceled_order = order.cancel(now)
            await self.uow.orders.update(canceled_order)
            await self.uow.commit()

            await self.audit_log.log_event(
                event_type="order.canceled",
                user_id=request.canceled_by,
                details={
                    "order_id": str(order.id),
                    "order_number": order.order_number,
                    "canceled_by": str(request.canceled_by),
                },
            )

            return _to_dto(canceled_order)
