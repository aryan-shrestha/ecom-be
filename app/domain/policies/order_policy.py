"""Order domain policy."""

from app.domain.entities.order import Order, OrderStatus, _VALID_TRANSITIONS
from app.domain.errors.domain_errors import (
    InvalidOrderTransitionError,
    OrderAlreadyCanceledError,
    OrderCancelForbiddenError,
)


class OrderPolicy:
    """Domain policy for order state transitions."""

    @staticmethod
    def validate_can_cancel(order: Order) -> None:
        """Ensure the order can be canceled."""
        if order.status == OrderStatus.CANCELED:
            raise OrderAlreadyCanceledError(f"Order {order.order_number} is already canceled")
        if not order.can_cancel():
            raise OrderCancelForbiddenError(
                f"Order {order.order_number} cannot be canceled in status: {order.status.value}"
            )

    @staticmethod
    def validate_transition(order: Order, new_status: OrderStatus) -> None:
        """Validate a generic status transition."""
        if not order.can_transition_to(new_status):
            allowed = [s.value for s in _VALID_TRANSITIONS.get(order.status, set())]
            raise InvalidOrderTransitionError(
                f"Cannot transition order from {order.status.value} to {new_status.value}. "
                f"Allowed: {allowed}"
            )
