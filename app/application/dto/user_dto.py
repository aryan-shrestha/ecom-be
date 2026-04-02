"""User DTOs."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.application.dto.role_dto import RoleListDTO


@dataclass
class UserDTO:
    """User data transfer object."""

    id: UUID
    first_name: str | None
    last_name: str | None
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    roles: Optional['RoleListDTO'] = None


@dataclass
class UserListResponse:
    """Response DTO for listing users."""

    users: list[UserDTO]
    total: int
    offset: int
    limit: int