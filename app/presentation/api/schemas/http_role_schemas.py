from uuid import UUID

from pydantic import BaseModel, Field

class RoleCreateRequestSchema(BaseModel):
    """Request schema for creating a role."""

    name: str = Field(max_length=50)

class RoleUpdateRequestSchema(BaseModel):
    """Request schema for updating a role."""

    name: str = Field(max_length=50)

class RoleResponseSchema(BaseModel):
    """Role response schema."""

    id: UUID
    name: str


class RoleListResponseSchema(BaseModel):
    """Response schema for listing roles."""

    roles: list[RoleResponseSchema]