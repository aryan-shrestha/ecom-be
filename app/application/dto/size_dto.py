from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class SizeDTO:
    """Variant size."""

    id: UUID
    product_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


@dataclass
class SizeCreateRequest:
    """Request to create a new size."""

    name: str
    product_id: UUID