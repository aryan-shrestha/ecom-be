"""Inventory domain entity."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Inventory:
    """Inventory tracking for product variant."""

    variant_id: UUID
    on_hand: int
    reserved: int
    allow_backorder: bool

    def __post_init__(self) -> None:
        """Validate inventory invariants."""
        if self.on_hand < 0:
            raise ValueError("On-hand quantity cannot be negative")
        if self.reserved < 0:
            raise ValueError("Reserved quantity cannot be negative")
        if self.reserved > self.on_hand:
            raise ValueError("Reserved quantity cannot exceed on-hand quantity")

    @property
    def available(self) -> int:
        """Calculate available quantity (on_hand - reserved)."""
        return self.on_hand - self.reserved

    def is_in_stock(self) -> bool:
        """Check if item is in stock."""
        return self.available > 0 or self.allow_backorder

    def adjust_on_hand(self, delta: int) -> "Inventory":
        """Return new inventory with adjusted on-hand quantity."""
        new_on_hand = self.on_hand + delta
        if new_on_hand < 0 and not self.allow_backorder:
            raise ValueError(
                f"Cannot adjust on-hand by {delta}. "
                f"Result would be {new_on_hand} (backorder not allowed)"
            )
        # Ensure reserved doesn't exceed new on_hand (if positive)
        new_reserved = min(self.reserved, new_on_hand) if new_on_hand >= 0 else 0
        return Inventory(
            variant_id=self.variant_id,
            on_hand=new_on_hand,
            reserved=new_reserved,
            allow_backorder=self.allow_backorder,
        )

    def reserve(self, quantity: int) -> "Inventory":
        """Reserve quantity for pending orders."""
        if quantity < 0:
            raise ValueError("Reserve quantity must be positive")
        new_reserved = self.reserved + quantity
        if new_reserved > self.on_hand:
            raise ValueError(
                f"Cannot reserve {quantity}. "
                f"Only {self.available} available (on_hand: {self.on_hand}, reserved: {self.reserved})"
            )
        return Inventory(
            variant_id=self.variant_id,
            on_hand=self.on_hand,
            reserved=new_reserved,
            allow_backorder=self.allow_backorder,
        )

    def release(self, quantity: int) -> "Inventory":
        """Release reserved quantity."""
        if quantity < 0:
            raise ValueError("Release quantity must be positive")
        new_reserved = self.reserved - quantity
        if new_reserved < 0:
            raise ValueError(f"Cannot release {quantity}. Only {self.reserved} reserved")
        return Inventory(
            variant_id=self.variant_id,
            on_hand=self.on_hand,
            reserved=new_reserved,
            allow_backorder=self.allow_backorder,
        )
