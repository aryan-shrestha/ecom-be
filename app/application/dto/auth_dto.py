"""Authentication DTOs for use-case inputs and outputs."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class RegisterRequest:
    """Input DTO for user registration."""

    email: str
    password: str


@dataclass
class RegisterResponse:
    """Output DTO for user registration."""

    user_id: UUID
    email: str


@dataclass
class LoginRequest:
    """Input DTO for user login."""

    email: str
    password: str
    ip: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class LoginResponse:
    """Output DTO for user login."""

    access_token: str
    refresh_token: str
    csrf_token: str
    token_type: str = "Bearer"


@dataclass
class RefreshRequest:
    """Input DTO for token refresh."""

    refresh_token: str
    csrf_token: str
    ip: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class RefreshResponse:
    """Output DTO for token refresh."""

    access_token: str
    refresh_token: str
    csrf_token: str
    token_type: str = "Bearer"


@dataclass
class LogoutRequest:
    """Input DTO for logout."""

    refresh_token: str
    csrf_token: str


@dataclass
class ChangePasswordRequest:
    """Input DTO for password change."""

    user_id: UUID
    old_password: str
    new_password: str
