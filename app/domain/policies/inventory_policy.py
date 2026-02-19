"""Inventory policy."""

from app.domain.entities.inventory import Inventory
from app.domain.errors.domain_errors import InsufficientStockError, InvalidStockAdjustmentError


class InventoryPolicy:
    """Domain policy for inventory management."""

    @staticmethod
    def validate_adjustment(inventory: Inventory, delta: int) -> None:
        """
        Validate stock adjustment.
        
        Raises:
            InvalidStockAdjustmentError: If adjustment is invalid
            InsufficientStockError: If adjustment would cause negative stock without backorder
        """
        if delta == 0:
            raise InvalidStockAdjustmentError("Stock adjustment delta cannot be zero")

        new_on_hand = inventory.on_hand + delta

        if new_on_hand < 0 and not inventory.allow_backorder:
            raise InsufficientStockError(
                f"Cannot adjust stock by {delta}. "
                f"Would result in {new_on_hand} (backorder not allowed). "
                f"Current on-hand: {inventory.on_hand}"
            )

    @staticmethod
    def validate_reservation(inventory: Inventory, quantity: int) -> None:
        """
        Validate stock reservation.
        
        Raises:
            InvalidStockAdjustmentError: If reservation quantity is invalid
            InsufficientStockError: If insufficient stock available
        """
        if quantity <= 0:
            raise InvalidStockAdjustmentError("Reservation quantity must be positive")

        if inventory.available < quantity:
            raise InsufficientStockError(
                f"Insufficient stock to reserve {quantity}. "
                f"Available: {inventory.available} "
                f"(on_hand: {inventory.on_hand}, reserved: {inventory.reserved})"
            )

    @staticmethod
    def validate_release(inventory: Inventory, quantity: int) -> None:
        """
        Validate stock release.
        
        Raises:
            InvalidStockAdjustmentError: If release is invalid
        """
        if quantity <= 0:
            raise InvalidStockAdjustmentError("Release quantity must be positive")

        if inventory.reserved < quantity:
            raise InvalidStockAdjustmentError(
                f"Cannot release {quantity}. Only {inventory.reserved} reserved"
            )
