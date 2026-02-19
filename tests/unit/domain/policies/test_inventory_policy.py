"""Unit tests for InventoryPolicy."""

import pytest
from uuid import uuid4

from app.domain.entities.inventory import Inventory
from app.domain.policies.inventory_policy import InventoryPolicy
from app.domain.errors.domain_errors import InvalidStockAdjustmentError, InsufficientStockError


class TestInventoryPolicy:
    """Test cases for InventoryPolicy."""

    def test_validate_adjustment_positive_delta(self):
        """Test that positive delta adjustment is valid."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        # Should not raise
        InventoryPolicy.validate_adjustment(inventory, delta=5)

    def test_validate_adjustment_negative_delta_with_sufficient_stock(self):
        """Test that negative delta is valid when sufficient stock available."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        # Should not raise (10 - 8 = 2 >= 0)
        InventoryPolicy.validate_adjustment(inventory, delta=-8)

    def test_validate_adjustment_negative_delta_insufficient_stock(self):
        """Test that negative delta raises error when insufficient stock."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        # Should raise (10 - 15 = -5 < 0)
        with pytest.raises(InvalidStockAdjustmentError) as exc_info:
            InventoryPolicy.validate_adjustment(inventory, delta=-15)

        assert "insufficient stock" in str(exc_info.value).lower()

    def test_validate_adjustment_negative_delta_with_backorder(self):
        """Test that negative delta is valid when backorders allowed."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=True,
        )

        # Should not raise even with negative result
        InventoryPolicy.validate_adjustment(inventory, delta=-15)

    def test_validate_adjustment_zero_delta(self):
        """Test that zero delta raises error."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        with pytest.raises(InvalidStockAdjustmentError) as exc_info:
            InventoryPolicy.validate_adjustment(inventory, delta=0)

        assert "zero" in str(exc_info.value).lower()

    def test_validate_reservation_with_available_stock(self):
        """Test that reservation is valid when stock is available."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        # Available = 10 - 2 = 8, reserving 5 should succeed
        InventoryPolicy.validate_reservation(inventory, quantity=5)

    def test_validate_reservation_insufficient_available(self):
        """Test that reservation raises error when insufficient available."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=8,
            allow_backorder=False,
        )

        # Available = 10 - 8 = 2, reserving 5 should fail
        with pytest.raises(InsufficientStockError) as exc_info:
            InventoryPolicy.validate_reservation(inventory, quantity=5)

        assert "insufficient stock" in str(exc_info.value).lower()

    def test_validate_reservation_exact_available(self):
        """Test that reservation works with exact available amount."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=7,
            allow_backorder=False,
        )

        # Available = 10 - 7 = 3, reserving 3 should succeed
        InventoryPolicy.validate_reservation(inventory, quantity=3)

    def test_validate_reservation_zero_quantity(self):
        """Test that zero quantity reservation raises error."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        with pytest.raises(InvalidStockAdjustmentError) as exc_info:
            InventoryPolicy.validate_reservation(inventory, quantity=0)

        assert "positive" in str(exc_info.value).lower()

    def test_validate_reservation_negative_quantity(self):
        """Test that negative quantity reservation raises error."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=2,
            allow_backorder=False,
        )

        with pytest.raises(InvalidStockAdjustmentError) as exc_info:
            InventoryPolicy.validate_reservation(inventory, quantity=-5)

        assert "positive" in str(exc_info.value).lower()

    def test_validate_release_valid(self):
        """Test that valid release is accepted."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=5,
            allow_backorder=False,
        )

        # Releasing 3 out of 5 reserved should succeed
        InventoryPolicy.validate_release(inventory, quantity=3)

    def test_validate_release_exact_reserved(self):
        """Test that releasing exact reserved amount works."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=5,
            allow_backorder=False,
        )

        # Releasing all 5 reserved should succeed
        InventoryPolicy.validate_release(inventory, quantity=5)

    def test_validate_release_more_than_reserved(self):
        """Test that releasing more than reserved raises error."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=5,
            allow_backorder=False,
        )

        # Releasing 7 when only 5 reserved should fail
        with pytest.raises(InvalidStockAdjustmentError) as exc_info:
            InventoryPolicy.validate_release(inventory, quantity=7)

        assert "reserved" in str(exc_info.value).lower()

    def test_validate_release_zero_quantity(self):
        """Test that zero quantity release raises error."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=5,
            allow_backorder=False,
        )

        with pytest.raises(InvalidStockAdjustmentError) as exc_info:
            InventoryPolicy.validate_release(inventory, quantity=0)

        assert "positive" in str(exc_info.value).lower()

    def test_validate_release_negative_quantity(self):
        """Test that negative quantity release raises error."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=5,
            allow_backorder=False,
        )

        with pytest.raises(InvalidStockAdjustmentError) as exc_info:
            InventoryPolicy.validate_release(inventory, quantity=-2)

        assert "positive" in str(exc_info.value).lower()

    def test_validate_release_from_zero_reserved(self):
        """Test that releasing from zero reserved raises error."""
        inventory = Inventory(
            variant_id=uuid4(),
            on_hand=10,
            reserved=0,
            allow_backorder=False,
        )

        with pytest.raises(InvalidStockAdjustmentError) as exc_info:
            InventoryPolicy.validate_release(inventory, quantity=1)

        assert "reserved" in str(exc_info.value).lower()

