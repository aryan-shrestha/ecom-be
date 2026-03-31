from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class CreateCategoryRequestSchema(BaseModel):
    """Request to create category."""

    name: str = Field(..., min_length=1, max_length=100)
    parent_id: Optional[UUID] = None


class UpdateCategoryRequestSchema(BaseModel):
    """Request to update category."""

    name: str = Field(..., min_length=1, max_length=100)
    parent_id: Optional[UUID] = None


class CategoryResponseSchema(BaseModel):
    """Category response."""

    id: UUID
    name: str
    slug: str
    parent_id: Optional[UUID]