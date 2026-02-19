"""Money value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    """
    Money value object representing monetary amount in minor units (cents).
    
    Amount is stored as integer to avoid floating-point precision issues.
    """

    amount: int  # Amount in minor units (e.g., cents for USD)
    currency: str

    def __post_init__(self) -> None:
        """Validate money value."""
        if not isinstance(self.amount, int):
            raise ValueError("Money amount must be an integer (minor units)")
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if not self.currency or not self.currency.strip():
            raise ValueError("Currency code cannot be empty")
        if len(self.currency) != 3:
            raise ValueError("Currency code must be 3 characters (ISO 4217)")
        if not self.currency.isupper():
            raise ValueError("Currency code must be uppercase")

    @classmethod
    def from_major_units(cls, amount: float, currency: str) -> "Money":
        """Create Money from major units (e.g., dollars)."""
        minor_amount = int(amount * 100)  # Convert to cents
        return cls(amount=minor_amount, currency=currency)

    def to_major_units(self) -> float:
        """Convert to major units (e.g., dollars)."""
        return self.amount / 100.0

    def __str__(self) -> str:
        """String representation."""
        return f"{self.to_major_units():.2f} {self.currency}"

    def __repr__(self) -> str:
        """Debug representation."""
        return f"Money(amount={self.amount}, currency='{self.currency}')"
