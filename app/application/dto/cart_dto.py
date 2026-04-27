"""Cart DTOs."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.application.dto.product_dto import MoneyDTO

@dataclass
class CartItemDTO:
    id: UUID
    cart_id: UUID
    variant_id: UUID
    product_id: UUID
    product_name: str
    product_slug: str
    variant_images: list[str]
    quantity: int
    unit_price_amount: int
    unit_price_currency: str
    line_subtotal_amount: int


@dataclass
class CartDTO:
    id: UUID
    status: str
    user_id: Optional[UUID]
    guest_token: Optional[str]
    items: list[CartItemDTO]
    subtotal_amount: int
    subtotal_currency: str
    created_at: datetime
    updated_at: datetime


# --- Request ---

@dataclass
class AddCartItemRequest:
    variant_id: UUID
    quantity: int
    # Actor identity – exactly one will be set
    user_id: Optional[UUID] = None
    guest_token: Optional[str] = None


@dataclass
class UpdateCartItemRequest:
    item_id: UUID
    quantity: int
    user_id: Optional[UUID] = None
    guest_token: Optional[str] = None


@dataclass
class RemoveCartItemRequest:
    item_id: UUID
    user_id: Optional[UUID] = None
    guest_token: Optional[str] = None


@dataclass
class GetCartRequest:
    user_id: Optional[UUID] = None
    guest_token: Optional[str] = None


@dataclass
class ClearCartRequest:
    user_id: Optional[UUID] = None
    guest_token: Optional[str] = None


@dataclass
class MergeGuestCartRequest:
    """Merge a guest cart into an authenticated user cart on login."""
    user_id: UUID
    guest_token: str
