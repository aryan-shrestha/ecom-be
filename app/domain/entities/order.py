"""Order domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from app.domain.value_objects.money import Money


class OrderStatus(Enum):
    """Order lifecycle status."""

    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELED = "CANCELED"


# Allowed forward transitions
_VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING_PAYMENT: {OrderStatus.PAID, OrderStatus.CANCELED},
    OrderStatus.PAID: {OrderStatus.PROCESSING, OrderStatus.CANCELED},
    OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELED: set(),
}

# Statuses that are too far along to cancel
_NON_CANCELABLE: set[OrderStatus] = {OrderStatus.SHIPPED, OrderStatus.DELIVERED}


@dataclass(frozen=True)
class OrderItem:
    """Snapshot line item inside an order."""

    id: UUID
    order_id: UUID
    variant_id: UUID
    product_name: str
    variant_sku: str
    variant_label: Optional[str]  # e.g. "Red / Large"
    unit_price: Money
    quantity: int

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise ValueError("Order item quantity must be at least 1")
        if not self.product_name:
            raise ValueError("product_name snapshot cannot be empty")

    @property
    def line_total(self) -> Money:
        return Money(amount=self.unit_price.amount * self.quantity, currency=self.unit_price.currency)


@dataclass(frozen=True)
class Order:
    """Order aggregate root."""

    id: UUID
    order_number: str
    status: OrderStatus
    user_id: Optional[UUID]
    guest_token: Optional[str]
    subtotal: Money
    grand_total: Money
    currency: str
    notes: Optional[str]
    shipping_address: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: tuple[OrderItem, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.user_id is None and self.guest_token is None:
            raise ValueError("Order must have either user_id or guest_token")
        if not self.order_number:
            raise ValueError("Order number cannot be empty")

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def can_cancel(self) -> bool:
        """Return True if the order can still be canceled."""
        return self.status not in _NON_CANCELABLE and self.status != OrderStatus.CANCELED

    def can_transition_to(self, new_status: OrderStatus) -> bool:
        return new_status in _VALID_TRANSITIONS.get(self.status, set())

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def transition_to(self, new_status: OrderStatus, updated_at: datetime) -> "Order":
        return _replace_order(self, status=new_status, updated_at=updated_at)

    def cancel(self, updated_at: datetime) -> "Order":
        return self.transition_to(OrderStatus.CANCELED, updated_at)


def _replace_order(order: Order, **changes) -> Order:
    return Order(
        id=changes.get("id", order.id),
        order_number=changes.get("order_number", order.order_number),
        status=changes.get("status", order.status),
        user_id=changes.get("user_id", order.user_id),
        guest_token=changes.get("guest_token", order.guest_token),
        subtotal=changes.get("subtotal", order.subtotal),
        grand_total=changes.get("grand_total", order.grand_total),
        currency=changes.get("currency", order.currency),
        notes=changes.get("notes", order.notes),
        shipping_address=changes.get("shipping_address", order.shipping_address),
        created_at=changes.get("created_at", order.created_at),
        updated_at=changes.get("updated_at", order.updated_at),
        items=changes.get("items", order.items),
    )
