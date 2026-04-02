from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.presentation.api.schemas.http_role_schemas import RoleListResponseSchema


class UserResponseSchema(BaseModel):
    """User response schema."""

    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    roles: RoleListResponseSchema | None = None


class UserListResponseSchema(BaseModel):
    """Response schema for listing users."""

    users: list[UserResponseSchema]
    total: int
    offset: int
    limit: int