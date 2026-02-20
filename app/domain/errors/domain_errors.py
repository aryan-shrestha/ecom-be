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


# Product-related errors


class ProductNotFoundError(DomainError):
    """Raised when product cannot be found."""


class ProductAlreadyExistsError(DomainError):
    """Raised when product with same slug already exists."""


class ProductPublishError(DomainError):
    """Raised when product cannot be published."""


class VariantNotFoundError(DomainError):
    """Raised when product variant cannot be found."""


class VariantAlreadyExistsError(DomainError):
    """Raised when variant with same SKU already exists."""


class CategoryNotFoundError(DomainError):
    """Raised when category cannot be found."""


class CategoryAlreadyExistsError(DomainError):
    """Raised when category with same slug already exists."""


class InventoryNotFoundError(DomainError):
    """Raised when inventory record cannot be found."""


class InsufficientStockError(DomainError):
    """Raised when requested quantity exceeds available stock."""


class InvalidStockAdjustmentError(DomainError):
    """Raised when stock adjustment is invalid."""


class ImageValidationError(DomainError):
    """Raised when image validation fails."""


class InvalidImageFormatError(DomainError):
    """Raised when image format is not allowed."""


class ImageTooLargeError(DomainError):
    """Raised when image file size exceeds limit."""


class ImageNotFoundError(DomainError):
    """Raised when image cannot be found."""


class ImageNotFoundError(DomainError):
    """Raised when product image cannot be found."""
