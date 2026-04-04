from uuid import UUID
from pydantic import BaseModel, Field

class PermissionCreateRequestSchema(BaseModel):
    """Request schema for creating a permission."""

    code: str = Field(max_length=50)

class PermissionResponseSchema(BaseModel):
    """Permission response schema."""

    id: UUID
    code: str

class PermissionListResponseSchema(BaseModel):
    """Response schema for listing permissions."""

    permissions: list[PermissionResponseSchema]

