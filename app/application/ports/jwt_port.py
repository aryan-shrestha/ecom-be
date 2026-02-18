"""JWT port interface - application boundary for JWT operations."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class JwtPort(ABC):
    """Port interface for JWT token operations."""

    @abstractmethod
    def issue_access_token(
        self, user_id: UUID, roles: list[str], token_version: int
    ) -> str:
        """
        Issue a new access JWT token.
        
        Args:
            user_id: User's unique identifier
            roles: List of role names
            token_version: Current user token version
        
        Returns:
            Signed JWT token string
        """
        ...

    @abstractmethod
    def verify_access_token(self, token: str) -> dict:
        """
        Verify and decode access token.
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded token claims
        
        Raises:
            Exception if token is invalid or expired
        """
        ...

    @abstractmethod
    def decode_token_unsafe(self, token: str) -> dict:
        """
        Decode token without verification (for inspection only).
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded token claims (unverified)
        """
        ...
