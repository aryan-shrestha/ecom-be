"""Product variant domain entity."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from app.domain.value_objects.money import Money
from app.domain.value_objects.sku import SKU


class VariantStatus(Enum):
    """Variant status."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

@dataclass(frozen=True)
class Color:
    """Variant color."""

    name: str
    hex_code: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Color name cannot be empty")

        object.__setattr__(self, "name", self.name.strip())

        if self.hex_code is not None:
            hex_code = self.hex_code.strip()

            if not hex_code.startswith("#") or len(hex_code) != 7:
                raise ValueError("Color hex code must be in format #RRGGBB")

            object.__setattr__(self, "hex_code", hex_code.upper())

@dataclass(frozen=True)
class ProductVariant:
    """Product variant entity."""

    id: UUID
    product_id: UUID
    sku: SKU
    barcode: Optional[str]
    status: VariantStatus
    price: Money
    compare_at_price: Optional[Money]
    cost: Optional[Money]
    color: Optional[Color]
    size: Optional[str]
    is_default: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Validate variant invariants."""
        if self.barcode and len(self.barcode) > 100:
            raise ValueError("Barcode cannot exceed 100 characters")
        if self.size and len(self.size) > 3:
            raise ValueError("Size cannot exceed 3 characters")
        # Compare at price should be same currency as price
        if self.compare_at_price and self.compare_at_price.currency != self.price.currency:
            raise ValueError("Compare at price must have same currency as price")
        if self.cost and self.cost.currency != self.price.currency:
            raise ValueError("Cost must have same currency as price")

    def is_active(self) -> bool:
        """Check if variant is active."""
        return self.status == VariantStatus.ACTIVE

    def deactivate(self, updated_at: datetime) -> "ProductVariant":
        """Deactivate variant."""
        return ProductVariant(
            id=self.id,
            product_id=self.product_id,
            sku=self.sku,
            barcode=self.barcode,
            status=VariantStatus.INACTIVE,
            price=self.price,
            compare_at_price=self.compare_at_price,
            cost=self.cost,
            color=self.color,
            size=self.size,
            is_default=self.is_default,
            created_at=self.created_at,
            updated_at=updated_at,
        )

    def update(
        self,
        barcode: Optional[str],
        status: VariantStatus,
        price: Money,
        compare_at_price: Optional[Money],
        cost: Optional[Money],
        color: Optional[Color],
        size: Optional[str],
        updated_at: datetime,
    ) -> "ProductVariant":
        """Return new variant with updated details."""
        return ProductVariant(
            id=self.id,
            product_id=self.product_id,
            sku=self.sku,  # SKU not changed in update
            barcode=barcode,
            status=status,
            price=price,
            compare_at_price=compare_at_price,
            cost=cost,
            color=color,
            size=size,
            is_default=self.is_default,
            created_at=self.created_at,
            updated_at=updated_at,
        )
