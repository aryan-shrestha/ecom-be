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


# Cart-related errors


class CartNotFoundError(DomainError):
    """Raised when cart cannot be found."""


class CartItemNotFoundError(DomainError):
    """Raised when cart item cannot be found."""


class CartAlreadyConvertedError(DomainError):
    """Raised when trying to modify a cart that has already been checked out."""


class CartItemQuantityError(DomainError):
    """Raised when cart item quantity is invalid."""


class VariantNotAvailableError(DomainError):
    """Raised when a variant is not available for purchase (inactive / product archived)."""


# Order-related errors


class OrderNotFoundError(DomainError):
    """Raised when order cannot be found."""


class OrderAlreadyCanceledError(DomainError):
    """Raised when trying to cancel an already-canceled order."""


class OrderCancelForbiddenError(DomainError):
    """Raised when trying to cancel an order in a non-cancelable state."""


class InvalidOrderTransitionError(DomainError):
    """Raised when an invalid order status transition is attempted."""


class EmptyCartError(DomainError):
    """Raised when checkout is attempted on an empty cart."""
