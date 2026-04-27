from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class ColorDTO:
    """Variant color."""

    name: str
    hex_value: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class ColorCreateRequest:
    """Request to create a new color."""

    name: str
    hex_value: Optional[str]
    product_id: UUID