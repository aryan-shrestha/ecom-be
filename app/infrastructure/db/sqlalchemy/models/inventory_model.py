"""Inventory SQLAlchemy model."""

import uuid

from sqlalchemy import Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.sqlalchemy.base import Base


class InventoryModel(Base):
    """Inventory ORM model."""

    __tablename__ = "inventory"

    variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        primary_key=True,
    )
    on_hand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    allow_backorder: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
