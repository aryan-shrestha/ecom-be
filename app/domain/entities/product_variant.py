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
    weight: Optional[int]  # grams
    length: Optional[int]  # millimeters
    width: Optional[int]  # millimeters
    height: Optional[int]  # millimeters
    is_default: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Validate variant invariants."""
        if self.barcode and len(self.barcode) > 100:
            raise ValueError("Barcode cannot exceed 100 characters")
        if self.weight is not None and self.weight < 0:
            raise ValueError("Weight cannot be negative")
        if self.length is not None and self.length < 0:
            raise ValueError("Length cannot be negative")
        if self.width is not None and self.width < 0:
            raise ValueError("Width cannot be negative")
        if self.height is not None and self.height < 0:
            raise ValueError("Height cannot be negative")
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
            weight=self.weight,
            length=self.length,
            width=self.width,
            height=self.height,
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
        weight: Optional[int],
        length: Optional[int],
        width: Optional[int],
        height: Optional[int],
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
            weight=weight,
            length=length,
            width=width,
            height=height,
            is_default=self.is_default,
            created_at=self.created_at,
            updated_at=updated_at,
        )
