from typing import Optional
from uuid import UUID

from pydantic import BaseModel

class RoleResponseSchema(BaseModel):
    """Role response schema."""

    id: UUID
    name: str


class RoleListResponseSchema(BaseModel):
    """Response schema for listing roles."""

    roles: list[RoleResponseSchema]