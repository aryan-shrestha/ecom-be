"""Token hasher implementation using HMAC-SHA256."""

import hmac
import secrets
from hashlib import sha256

from app.application.ports.crypto_port import TokenHasherPort


class HmacTokenHasher(TokenHasherPort):
    """Token hasher using HMAC-SHA256."""

    def __init__(self, secret: str) -> None:
        self.secret = secret.encode()

    def generate_token(self) -> str:
        """Generate a cryptographically secure random token."""
        return secrets.token_urlsafe(32)

    def hash_token(self, token: str) -> str:
        """Hash a token using HMAC-SHA256."""
        return hmac.new(self.secret, token.encode(), sha256).hexdigest()

    def verify_token(self, token: str, token_hash: str) -> bool:
        """Verify token against hash."""
        computed_hash = self.hash_token(token)
        return hmac.compare_digest(computed_hash, token_hash)
