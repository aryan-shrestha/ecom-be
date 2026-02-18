"""Application layer errors."""


class ApplicationError(Exception):
    """Base application error."""


class AuthenticationFailedError(ApplicationError):
    """Raised when authentication fails."""


class TokenExpiredError(ApplicationError):
    """Raised when token has expired."""


class TokenInvalidError(ApplicationError):
    """Raised when token is invalid."""


class TokenVersionMismatchError(ApplicationError):
    """Raised when token version doesn't match user's current version."""


class PermissionDeniedError(ApplicationError):
    """Raised when user lacks required permission."""


class ValidationError(ApplicationError):
    """Raised when input validation fails."""


class ResourceNotFoundError(ApplicationError):
    """Raised when requested resource cannot be found."""


class ConflictError(ApplicationError):
    """Raised when operation conflicts with current state."""
