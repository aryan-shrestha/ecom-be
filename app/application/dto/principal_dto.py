"""Principal DTO representing authenticated user."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class PrincipalDTO:
    """
    Data transfer object representing an authenticated principal.
    
    Used to pass authentication context across application boundaries.
    """
    first_name: str
    last_name: str
    user_id: UUID
    email: str
    roles: list[str]
    token_version: int
    is_active: bool
