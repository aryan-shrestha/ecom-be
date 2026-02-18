"""Password policy - domain service."""


class PasswordPolicy:
    """
    Domain service for enforcing password requirements.
    
    Pure domain logic with no external dependencies.
    """

    MIN_LENGTH = 8
    MAX_LENGTH = 128

    @classmethod
    def validate(cls, password: str) -> None:
        """
        Validate password against policy.
        
        Raises ValueError if password doesn't meet requirements.
        """
        if not password:
            raise ValueError("Password cannot be empty")

        if len(password) < cls.MIN_LENGTH:
            raise ValueError(f"Password must be at least {cls.MIN_LENGTH} characters")

        if len(password) > cls.MAX_LENGTH:
            raise ValueError(f"Password cannot exceed {cls.MAX_LENGTH} characters")

        # Require at least one digit
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least one digit")

        # Require at least one letter
        if not any(char.isalpha() for char in password):
            raise ValueError("Password must contain at least one letter")

    @classmethod
    def is_valid(cls, password: str) -> bool:
        """Check if password meets policy (returns boolean instead of raising)."""
        try:
            cls.validate(password)
            return True
        except ValueError:
            return False
