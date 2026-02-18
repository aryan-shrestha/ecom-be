"""Application configuration using Pydantic Settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ecom_db"
    )

    # JWT Configuration
    jwt_issuer: str = Field(default="ecom-auth-service")
    jwt_audience: str = Field(default="ecom-api")
    jwt_algorithm: str = Field(default="RS256")
    jwt_access_token_ttl_minutes: int = Field(default=10)
    jwt_active_kid: str = Field(default="key-2024-01")

    # JWT Keys
    jwt_private_key_path: Optional[Path] = Field(default=None)
    jwt_public_key_path: Optional[Path] = Field(default=None)
    jwt_private_key_pem: Optional[str] = Field(default=None)
    jwt_public_key_pem: Optional[str] = Field(default=None)

    # Refresh Token
    refresh_token_ttl_days: int = Field(default=14)
    refresh_token_hmac_secret: str = Field(
        default="replace-with-secure-random-secret-min-32-chars"
    )

    # Cookie Settings
    cookie_secure: bool = Field(default=False)
    cookie_domain: str = Field(default="localhost")

    # Rate Limiting
    rate_limit_login_max_requests: int = Field(default=5)
    rate_limit_login_window_seconds: int = Field(default=60)
    rate_limit_refresh_max_requests: int = Field(default=10)
    rate_limit_refresh_window_seconds: int = Field(default=60)

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )

    # Application
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    def get_jwt_private_key(self) -> str:
        """Load JWT private key from PEM string or file."""
        if self.jwt_private_key_pem:
            return self.jwt_private_key_pem
        if self.jwt_private_key_path and self.jwt_private_key_path.exists():
            return self.jwt_private_key_path.read_text()
        raise ValueError("JWT private key not configured (set JWT_PRIVATE_KEY_PEM or JWT_PRIVATE_KEY_PATH)")

    def get_jwt_public_key(self) -> str:
        """Load JWT public key from PEM string or file."""
        if self.jwt_public_key_pem:
            return self.jwt_public_key_pem
        if self.jwt_public_key_path and self.jwt_public_key_path.exists():
            return self.jwt_public_key_path.read_text()
        raise ValueError("JWT public key not configured (set JWT_PUBLIC_KEY_PEM or JWT_PUBLIC_KEY_PATH)")


# Global settings instance
settings = Settings()
