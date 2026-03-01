"""HTTP request/response schemas for order endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OrderItemResponseSchema(BaseModel):
    id: UUID
    variant_id: UUID
    product_name: str
    variant_sku: str
    variant_label: Optional[str] = None
    unit_price_amount: int
    unit_price_currency: str
    quantity: int
    line_total_amount: int


class OrderResponseSchema(BaseModel):
    id: UUID
    order_number: str
    status: str
    user_id: Optional[UUID] = None
    subtotal_amount: int
    grand_total_amount: int
    currency: str
    notes: Optional[str] = None
    shipping_address: Optional[str] = None
    items: list[OrderItemResponseSchema]
    created_at: datetime
    updated_at: datetime


class OrderListResponseSchema(BaseModel):
    orders: list[OrderResponseSchema]
    total: int
    offset: int
    limit: int


class CheckoutRequestSchema(BaseModel):
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
