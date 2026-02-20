"""Product variant SQLAlchemy model."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.sqlalchemy.base import Base


class ProductVariantModel(Base):
    """Product variant ORM model."""

    __tablename__ = "product_variants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    # Price stored as integer (minor units) and currency code
    price_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    price_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    
    # Optional compare at price
    compare_at_price_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    compare_at_price_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    
    # Optional cost
    cost_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    
    # Dimensions - map to actual DB column names
    weight: Mapped[Optional[int]] = mapped_column("weight_grams", Integer, nullable=True)  # grams
    length: Mapped[Optional[int]] = mapped_column("length_mm", Integer, nullable=True)  # mm
    width: Mapped[Optional[int]] = mapped_column("width_mm", Integer, nullable=True)  # mm
    height: Mapped[Optional[int]] = mapped_column("height_mm", Integer, nullable=True)  # mm
    
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
