"""Password hasher implementation using argon2."""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.application.ports.crypto_port import PasswordHasherPort


class Argon2PasswordHasher(PasswordHasherPort):
    """Password hasher using Argon2id."""

    def __init__(self) -> None:
        self.hasher = PasswordHasher()

    def hash_password(self, password: str) -> str:
        """Hash a password securely using Argon2."""
        return self.hasher.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        try:
            self.hasher.verify(password_hash, password)
            return True
        except VerifyMismatchError:
            return False
