"""
Size SQLALchemy Model
"""
import uuid
from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.sqlalchemy.base import Base


class SizeModel(Base):
    """Size ORM model."""

    __tablename__ = "sizes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(
        uuid.UUID(as_uuid=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)