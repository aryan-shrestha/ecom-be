"""Permission SQLAlchemy model."""

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.sqlalchemy.base import Base


class PermissionModel(Base):
    """Permission ORM model."""

    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
