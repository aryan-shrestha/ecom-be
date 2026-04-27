"""
Color SQLAlchemy model representing the colors table in the database.
"""

import uuid
from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.sqlalchemy.base import Base


class ColorModel(Base):
    """
    Color ORM model representing a color option for product variants.
    """
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    hex_value: Mapped[str] = mapped_column(String(7), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)