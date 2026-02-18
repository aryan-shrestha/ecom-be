"""Role-Permission association SQLAlchemy model."""

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.sqlalchemy.base import Base


class RolePermissionModel(Base):
    """Role-Permission association ORM model."""

    __tablename__ = "role_permissions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)
