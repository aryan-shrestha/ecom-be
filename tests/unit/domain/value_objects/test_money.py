"""Unit tests for Money value object."""

import pytest

from app.domain.value_objects.money import Money


class TestMoney:
    """Test cases for Money value object."""

    def test_create_money_valid(self):
        """Test creating valid Money instance."""
        money = Money(amount=1550, currency="USD")

        assert money.amount == 1550
        assert money.currency == "USD"

    def test_create_money_zero_amount(self):
        """Test creating Money with zero amount."""
        money = Money(amount=0, currency="USD")

        assert money.amount == 0
        assert money.currency == "USD"

    def test_create_money_negative_amount(self):
        """Test that negative amount raises error."""
        with pytest.raises(ValueError) as exc_info:
            Money(amount=-100, currency="USD")

        assert "negative" in str(exc_info.value).lower()

    def test_currency_uppercase_validation(self):
        """Test that currency must be uppercase 3 letters."""
        # Valid
        Money(amount=100, currency="USD")
        Money(amount=100, currency="EUR")
        Money(amount=100, currency="GBP")

        # Invalid - lowercase
        with pytest.raises(ValueError):
            Money(amount=100, currency="usd")

        # Invalid - too short
        with pytest.raises(ValueError):
            Money(amount=100, currency="US")

        # Invalid - too long
        with pytest.raises(ValueError):
            Money(amount=100, currency="USDD")

        # Invalid - contains non-letters
        with pytest.raises(ValueError):
            Money(amount=100, currency="US1")

    def test_from_major_units(self):
        """Test creating Money from major units (dollars, euros, etc.)."""
        money = Money.from_major_units(15.50, "USD")

        assert money.amount == 1550
        assert money.currency == "USD"

    def test_from_major_units_whole_number(self):
        """Test creating Money from whole number major units."""
        money = Money.from_major_units(10, "USD")

        assert money.amount == 1000
        assert money.currency == "USD"

    def test_from_major_units_precision(self):
        """Test that from_major_units handles precision correctly."""
        # Common case: 2 decimal places
        money = Money.from_major_units(9.99, "USD")
        assert money.amount == 999

        # Edge case: many decimal places (should round)
        money = Money.from_major_units(9.999, "USD")
        assert money.amount == 1000  # Rounds to 10.00

    def test_to_major_units(self):
        """Test converting Money to major units."""
        money = Money(amount=1550, currency="USD")

        assert money.to_major_units() == 15.50

    def test_to_major_units_whole_number(self):
        """Test converting whole number amount to major units."""
        money = Money(amount=1000, currency="USD")

        assert money.to_major_units() == 10.0

    def test_to_major_units_fractional(self):
        """Test converting fractional amount to major units."""
        money = Money(amount=1, currency="USD")

        assert money.to_major_units() == 0.01

    def test_money_equality(self):
        """Test Money equality comparison."""
        money1 = Money(amount=1000, currency="USD")
        money2 = Money(amount=1000, currency="USD")
        money3 = Money(amount=1500, currency="USD")
        money4 = Money(amount=1000, currency="EUR")

        assert money1 == money2
        assert money1 != money3
        assert money1 != money4

    def test_money_immutability(self):
        """Test that Money is immutable (frozen dataclass)."""
        money = Money(amount=1000, currency="USD")

        with pytest.raises(AttributeError):
            money.amount = 2000

        with pytest.raises(AttributeError):
            money.currency = "EUR"

    def test_roundtrip_conversion(self):
        """Test that converting to and from major units preserves value."""
        original_amount = 49.99
        money = Money.from_major_units(original_amount, "USD")
        converted_back = money.to_major_units()

        assert abs(converted_back - original_amount) < 0.01

    def test_zero_money(self):
        """Test creating and converting zero money."""
        money = Money.from_major_units(0.0, "USD")

        assert money.amount == 0
        assert money.to_major_units() == 0.0

    def test_large_amount(self):
        """Test handling large amounts."""
        money = Money.from_major_units(999999.99, "USD")

        assert money.amount == 99999999
        assert money.to_major_units() == 999999.99

