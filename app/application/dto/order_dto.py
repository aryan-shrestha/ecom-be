"""Order DTOs."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class OrderItemDTO:
    id: UUID
    order_id: UUID
    variant_id: UUID
    product_name: str
    variant_sku: str
    variant_label: Optional[str]
    unit_price_amount: int
    unit_price_currency: str
    quantity: int
    line_total_amount: int


@dataclass
class OrderDTO:
    id: UUID
    order_number: str
    status: str
    user_id: Optional[UUID]
    guest_token: Optional[str]
    subtotal_amount: int
    grand_total_amount: int
    currency: str
    notes: Optional[str]
    shipping_address: Optional[str]
    items: list[OrderItemDTO]
    created_at: datetime
    updated_at: datetime


@dataclass
class OrderListDTO:
    orders: list[OrderDTO]
    total: int
    offset: int
    limit: int


# --- Requests ---

@dataclass
class CheckoutRequest:
    idempotency_key: str
    user_id: Optional[UUID] = None
    guest_token: Optional[str] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class GetMyOrdersRequest:
    user_id: UUID
    offset: int = 0
    limit: int = 20


@dataclass
class GetOrderDetailRequest:
    order_id: UUID
    user_id: UUID  # Ownership check


@dataclass
class AdminListOrdersRequest:
    offset: int = 0
    limit: int = 20
    status: Optional[str] = None
    user_id: Optional[UUID] = None
    order_number: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


@dataclass
class AdminCancelOrderRequest:
    order_id: UUID
    canceled_by: UUID
