from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class SizeDTO:
    """Variant size."""

    name: str
    product_id: UUID
    created_at: datetime
    updated_at: datetime


@dataclass
class SizeCreateRequest:
    """Request to create a new size."""

    name: str
    product_id: UUID