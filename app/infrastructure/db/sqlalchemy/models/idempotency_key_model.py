"""IdempotencyKey SQLAlchemy model."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.sqlalchemy.base import Base


class IdempotencyKeyModel(Base):
    """Idempotency key ORM model for checkout deduplication."""

    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint(
            "scope", "actor_identifier", "key",
            name="uq_idempotency_scope_actor_key"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    actor_identifier: Mapped[str] = mapped_column(String(128), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
