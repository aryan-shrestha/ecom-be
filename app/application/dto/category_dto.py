"Category DTO"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

@dataclass
class CategoryDTO:
    id: UUID
    name: str
    slug: str
    parent_id: Optional[UUID]
    
@dataclass
class CreateCategoryRequest:
    """Request to create category."""

    name: str
    parent_id: Optional[UUID] = None

@dataclass
class UpdateCategoryRequest:
    id: UUID
    name: str
    parent_id: Optional[UUID]
    updated_by: Optional[UUID] = None