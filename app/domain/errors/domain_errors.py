"""Domain-specific errors."""


class DomainError(Exception):
    """Base domain error."""


class InvalidEmailError(DomainError):
    """Raised when email format is invalid."""


class InvalidPasswordError(DomainError):
    """Raised when password doesn't meet policy requirements."""


class UserAlreadyExistsError(DomainError):
    """Raised when attempting to register with an existing email."""


class UserNotFoundError(DomainError):
    """Raised when user cannot be found."""


class InvalidCredentialsError(DomainError):
    """Raised when login credentials are invalid."""


class UserNotActiveError(DomainError):
    """Raised when user account is not active."""


class RefreshTokenNotFoundError(DomainError):
    """Raised when refresh token cannot be found."""


class RefreshTokenExpiredError(DomainError):
    """Raised when refresh token has expired."""


class RefreshTokenRevokedError(DomainError):
    """Raised when refresh token has been revoked."""


class RefreshTokenReuseDetectedError(DomainError):
    """Raised when refresh token reuse is detected (security threat)."""


class InsufficientPermissionsError(DomainError):
    """Raised when user lacks required permissions."""


class RoleNotFoundError(DomainError):
    """Raised when role cannot be found."""


class PermissionNotFoundError(DomainError):
    """Raised when permission cannot be found."""
