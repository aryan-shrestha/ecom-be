from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class ColorDTO:
    """Variant color."""

    id: UUID
    product_id: UUID
    name: str
    hex_value: str
    created_at: datetime
    updated_at: datetime


@dataclass
class ColorCreateRequest:
    """Request to create a new color."""

    name: str
    hex_value: str
    product_id: UUID