"""Cryptography ports for password and token hashing."""

from abc import ABC, abstractmethod


class PasswordHasherPort(ABC):
    """Port interface for password hashing operations."""

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash a password securely."""
        ...

    @abstractmethod
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        ...


class TokenHasherPort(ABC):
    """Port interface for refresh token generation and hashing."""

    @abstractmethod
    def generate_token(self) -> str:
        """
        Generate a cryptographically secure random token.
        
        Returns:
            URL-safe base64 token string
        """
        ...

    @abstractmethod
    def hash_token(self, token: str) -> str:
        """
        Hash a token using HMAC-SHA256.
        
        Args:
            token: Plain token string
        
        Returns:
            Hex-encoded hash
        """
        ...

    @abstractmethod
    def verify_token(self, token: str, token_hash: str) -> bool:
        """
        Verify token against hash.
        
        Args:
            token: Plain token string
            token_hash: Hex-encoded hash
        
        Returns:
            True if token matches hash
        """
        ...
