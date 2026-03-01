"""Order SQLAlchemy model."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.sqlalchemy.base import Base


class OrderModel(Base):
    """Order ORM model."""

    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    guest_token: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    subtotal_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    grand_total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipping_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
