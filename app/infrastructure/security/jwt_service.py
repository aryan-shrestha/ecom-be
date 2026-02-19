"""JWT service implementation using PyJWT with RS256."""

import uuid
from datetime import timedelta, timezone
from typing import Any

import jwt

from app.application.ports.clock_port import ClockPort
from app.application.ports.jwt_port import JwtPort


class JwtService(JwtPort):
    """JWT service implementation using RS256 algorithm."""

    def __init__(
        self,
        private_key: str,
        public_key: str,
        algorithm: str,
        issuer: str,
        audience: str,
        kid: str,
        access_token_ttl_minutes: int,
        clock: ClockPort,
    ) -> None:
        self.private_key = private_key
        self.public_key = public_key
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience
        self.kid = kid
        self.access_token_ttl_minutes = access_token_ttl_minutes
        self.clock = clock

    def issue_access_token(
        self, user_id: uuid.UUID, roles: list[str], token_version: int
    ) -> str:
        """Issue a new access JWT token."""
        now = self.clock.now()
        exp = now + timedelta(minutes=self.access_token_ttl_minutes)

        # Convert naive UTC datetime to timestamp
        # clock.now() returns naive datetime representing UTC, so we add timezone info
        claims = {
            "sub": str(user_id),
            "roles": roles,
            "ver": token_version,
            "jti": str(uuid.uuid4()),
            "iss": self.issuer,
            "aud": self.audience,
            "iat": int(now.replace(tzinfo=timezone.utc).timestamp()),
            "exp": int(exp.replace(tzinfo=timezone.utc).timestamp()),
        }

        headers = {"kid": self.kid}

        return jwt.encode(
            claims, self.private_key, algorithm=self.algorithm, headers=headers
        )

    def verify_access_token(self, token: str) -> dict[str, Any]:
        """Verify and decode access token."""
        return jwt.decode(
            token,
            self.public_key,
            algorithms=[self.algorithm],
            issuer=self.issuer,
            audience=self.audience,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )

    def decode_token_unsafe(self, token: str) -> dict[str, Any]:
        """Decode token without verification (for inspection only)."""
        return jwt.decode(token, options={"verify_signature": False})
