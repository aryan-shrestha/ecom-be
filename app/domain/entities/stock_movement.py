"""Stock movement domain entity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class StockMovement:
    """Stock movement audit record."""

    id: UUID
    variant_id: UUID
    delta: int  # Positive for additions, negative for reductions
    reason: str
    note: Optional[str]
    created_at: datetime
    created_by: Optional[UUID]

    def __post_init__(self) -> None:
        """Validate stock movement."""
        if self.delta == 0:
            raise ValueError("Stock movement delta cannot be zero")
        if not self.reason or not self.reason.strip():
            raise ValueError("Stock movement reason cannot be empty")
        if len(self.reason) > 100:
            raise ValueError("Reason cannot exceed 100 characters")
        if self.note and len(self.note) > 500:
            raise ValueError("Note cannot exceed 500 characters")

    def is_increase(self) -> bool:
        """Check if movement increases stock."""
        return self.delta > 0

    def is_decrease(self) -> bool:
        """Check if movement decreases stock."""
        return self.delta < 0
