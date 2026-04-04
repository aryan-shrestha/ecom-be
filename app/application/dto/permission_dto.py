from dataclasses import dataclass
from uuid import UUID

@dataclass
class PermissionDTO:
    id: UUID
    code: str


@dataclass
class PermissionListDTO:
    permissions: list[PermissionDTO]