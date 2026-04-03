from dataclasses import dataclass
from uuid import UUID

@dataclass
class RoleDTO:
    """Role data transfer object."""

    id: UUID
    name: str
    

@dataclass
class RoleListDTO:
    """Response DTO for listing roles."""

    roles: list[RoleDTO]
