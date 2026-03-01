"""Cart domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class CartStatus(Enum):
    """Cart lifecycle status."""

    ACTIVE = "ACTIVE"
    CONVERTED = "CONVERTED"  # Checked out → order created
    ABANDONED = "ABANDONED"  # Expired / manually cleared


@dataclass(frozen=True)
class CartItem:
    """A single line item in a cart."""

    id: UUID
    cart_id: UUID
    variant_id: UUID
    quantity: int

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise ValueError("Cart item quantity must be at least 1")

    def with_quantity(self, quantity: int) -> "CartItem":
        """Return new CartItem with updated quantity."""
        return CartItem(
            id=self.id,
            cart_id=self.cart_id,
            variant_id=self.variant_id,
            quantity=quantity,
        )


@dataclass(frozen=True)
class Cart:
    """Cart aggregate root."""

    id: UUID
    status: CartStatus
    user_id: Optional[UUID]
    guest_token: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: tuple[CartItem, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.user_id is None and self.guest_token is None:
            raise ValueError("Cart must have either a user_id or a guest_token")

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def is_active(self) -> bool:
        return self.status == CartStatus.ACTIVE

    def is_converted(self) -> bool:
        return self.status == CartStatus.CONVERTED

    # ------------------------------------------------------------------
    # Item helpers
    # ------------------------------------------------------------------

    def find_item_by_id(self, item_id: UUID) -> Optional[CartItem]:
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def find_item_by_variant(self, variant_id: UUID) -> Optional[CartItem]:
        for item in self.items:
            if item.variant_id == variant_id:
                return item
        return None

    # ------------------------------------------------------------------
    # Mutations (return new Cart – immutable pattern)
    # ------------------------------------------------------------------

    def add_item(self, new_item: CartItem, updated_at: datetime) -> "Cart":
        """Add item (or increase qty if variant already present)."""
        existing = self.find_item_by_variant(new_item.variant_id)
        if existing:
            merged = existing.with_quantity(existing.quantity + new_item.quantity)
            new_items = tuple(
                merged if i.variant_id == new_item.variant_id else i
                for i in self.items
            )
        else:
            new_items = self.items + (new_item,)
        return _replace(self, items=new_items, updated_at=updated_at)

    def update_item_quantity(
        self, item_id: UUID, quantity: int, updated_at: datetime
    ) -> "Cart":
        """Replace quantity for a specific item."""
        new_items = tuple(
            i.with_quantity(quantity) if i.id == item_id else i for i in self.items
        )
        return _replace(self, items=new_items, updated_at=updated_at)

    def remove_item(self, item_id: UUID, updated_at: datetime) -> "Cart":
        """Remove item from cart."""
        new_items = tuple(i for i in self.items if i.id != item_id)
        return _replace(self, items=new_items, updated_at=updated_at)

    def clear(self, updated_at: datetime) -> "Cart":
        """Remove all items."""
        return _replace(self, items=(), updated_at=updated_at)

    def convert(self, updated_at: datetime) -> "Cart":
        """Mark cart as converted after successful checkout."""
        return _replace(self, status=CartStatus.CONVERTED, updated_at=updated_at)

    def abandon(self, updated_at: datetime) -> "Cart":
        """Mark cart as abandoned."""
        return _replace(self, status=CartStatus.ABANDONED, updated_at=updated_at)


# ---------------------------------------------------------------------------
# Helper: frozen dataclass equivalent of dataclasses.replace
# ---------------------------------------------------------------------------

def _replace(cart: Cart, **changes) -> Cart:
    """Return a new Cart with the given fields replaced."""
    return Cart(
        id=changes.get("id", cart.id),
        status=changes.get("status", cart.status),
        user_id=changes.get("user_id", cart.user_id),
        guest_token=changes.get("guest_token", cart.guest_token),
        created_at=changes.get("created_at", cart.created_at),
        updated_at=changes.get("updated_at", cart.updated_at),
        items=changes.get("items", cart.items),
    )
