"""HTTP request/response schemas for authentication endpoints."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequestSchema(BaseModel):
    """Request schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterResponseSchema(BaseModel):
    """Response schema for user registration."""

    user_id: str
    email: str


class LoginRequestSchema(BaseModel):
    """Request schema for user login."""

    email: EmailStr
    password: str


class LoginResponseSchema(BaseModel):
    """Response schema for user login."""

    access_token: str
    token_type: str = "Bearer"


class RefreshResponseSchema(BaseModel):
    """Response schema for token refresh."""

    access_token: str
    token_type: str = "Bearer"


class ChangePasswordRequestSchema(BaseModel):
    """Request schema for password change."""

    old_password: str
    new_password: str = Field(min_length=8, max_length=128)


class MessageResponseSchema(BaseModel):
    """Generic message response."""

    message: str


class ErrorResponseSchema(BaseModel):
    """Error response schema."""

    detail: str


class PrincipalResponseSchema(BaseModel):
    """Response schema for current principal info."""

    user_id: str
    email: str
    roles: list[str]
    is_active: bool


class AssignRoleRequestSchema(BaseModel):
    """Request schema for assigning role to user."""

    user_id: str
    role_name: str
