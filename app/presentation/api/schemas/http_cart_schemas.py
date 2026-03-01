"""HTTP request/response schemas for cart endpoints."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CartItemResponseSchema(BaseModel):
    id: UUID
    cart_id: UUID
    variant_id: UUID
    quantity: int
    unit_price_amount: int
    unit_price_currency: str
    line_subtotal_amount: int


class CartResponseSchema(BaseModel):
    id: UUID
    status: str
    user_id: Optional[UUID] = None
    items: list[CartItemResponseSchema]
    subtotal_amount: int
    subtotal_currency: str


class AddCartItemRequestSchema(BaseModel):
    variant_id: UUID
    quantity: int = Field(..., ge=1, le=100)


class UpdateCartItemRequestSchema(BaseModel):
    quantity: int = Field(..., ge=1, le=100)
