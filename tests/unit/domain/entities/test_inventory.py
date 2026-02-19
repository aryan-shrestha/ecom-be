"""Unit tests for Inventory entity."""

import pytest
from uuid import uuid4

from app.domain.entities.inventory import Inventory
from app.domain.errors.domain_errors import InvalidStockAdjustmentError, InsufficientStockError


class TestInventory:
    """Test cases for Inventory entity."""

    def test_create_inventory(self):
        """Test creating inventory instance."""
        variant_id = uuid4()
        inventory = Inventory(
            variant_id=variant_id,
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        assert inventory.variant_id == variant_id
        assert inventory.on_hand == 10
        assert inventory.reserved == 2
        assert inventory.allow_backorder is False

    def test_available_property(self):
        """Test that available is computed correctly."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=3,
            allow_backorder=False,
        )

        assert inventory.available == 7  # 10 - 3

    def test_available_property_zero_reserved(self):
        """Test available when no reservations."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=0,
            allow_backorder=False,
        )

        assert inventory.available == 10

    def test_available_property_all_reserved(self):
        """Test available when all stock is reserved."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=10,
            allow_backorder=False,
        )

        assert inventory.available == 0

    def test_adjust_on_hand_positive(self):
        """Test increasing on_hand stock."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        updated = inventory.adjust_on_hand(5)

        assert updated.on_hand == 15
        assert updated.reserved == 2  # Unchanged

    def test_adjust_on_hand_negative(self):
        """Test decreasing on_hand stock."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        updated = inventory.adjust_on_hand(-3)

        assert updated.on_hand == 7
        assert updated.reserved == 2

    def test_adjust_on_hand_to_zero(self):
        """Test adjusting on_hand to exactly zero."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=0,
            allow_backorder=False,
        )

        updated = inventory.adjust_on_hand(-10)

        assert updated.on_hand == 0

    def test_adjust_on_hand_zero_delta_raises_error(self):
        """Test that zero delta raises error."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        with pytest.raises(InvalidStockAdjustmentError):
            inventory.adjust_on_hand(0)

    def test_adjust_on_hand_insufficient_stock_raises_error(self):
        """Test that adjusting below zero raises error when backorder not allowed."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        with pytest.raises(InvalidStockAdjustmentError):
            inventory.adjust_on_hand(-15)

    def test_adjust_on_hand_negative_with_backorder(self):
        """Test that negative stock is allowed with backorder."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=True,
        )

        updated = inventory.adjust_on_hand(-15)

        assert updated.on_hand == -5
        assert updated.available == -7  # -5 - 2

    def test_reserve_valid_quantity(self):
        """Test reserving available stock."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        updated = inventory.reserve(5)

        assert updated.on_hand == 10  # Unchanged
        assert updated.reserved == 7  # 2 + 5
        assert updated.available == 3  # 10 - 7

    def test_reserve_all_available(self):
        """Test reserving all available stock."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        updated = inventory.reserve(8)

        assert updated.on_hand == 10
        assert updated.reserved == 10
        assert updated.available == 0

    def test_reserve_insufficient_available_raises_error(self):
        """Test that reserving more than available raises error."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=8,
            allow_backorder=False,
        )

        # Available = 2, trying to reserve 5
        with pytest.raises(InsufficientStockError):
            inventory.reserve(5)

    def test_reserve_zero_raises_error(self):
        """Test that reserving zero quantity raises error."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        with pytest.raises(InvalidStockAdjustmentError):
            inventory.reserve(0)

    def test_reserve_negative_raises_error(self):
        """Test that reserving negative quantity raises error."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        with pytest.raises(InvalidStockAdjustmentError):
            inventory.reserve(-5)

    def test_release_valid_quantity(self):
        """Test releasing reserved stock."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=5,
            allow_backorder=False,
        )

        updated = inventory.release(3)

        assert updated.on_hand == 10  # Unchanged
        assert updated.reserved == 2  # 5 - 3
        assert updated.available == 8  # 10 - 2

    def test_release_all_reserved(self):
        """Test releasing all reserved stock."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=5,
            allow_backorder=False,
        )

        updated = inventory.release(5)

        assert updated.on_hand == 10
        assert updated.reserved == 0
        assert updated.available == 10

    def test_release_more_than_reserved_raises_error(self):
        """Test that releasing more than reserved raises error."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=5,
            allow_backorder=False,
        )

        with pytest.raises(InvalidStockAdjustmentError):
            inventory.release(7)

    def test_release_zero_raises_error(self):
        """Test that releasing zero quantity raises error."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=5,
            allow_backorder=False,
        )

        with pytest.raises(InvalidStockAdjustmentError):
            inventory.release(0)

    def test_release_negative_raises_error(self):
        """Test that releasing negative quantity raises error."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=5,
            allow_backorder=False,
        )

        with pytest.raises(InvalidStockAdjustmentError):
            inventory.release(-2)

    def test_inventory_immutability(self):
        """Test that inventory operations return new instances."""
        original = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        updated = original.adjust_on_hand(5)

        # Original unchanged
        assert original.on_hand == 10
        # New instance created
        assert updated.on_hand == 15
        assert updated is not original

