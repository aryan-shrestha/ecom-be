"""RBAC policy - domain service for permission checking."""

from app.domain.entities.permission import Permission


class RbacPolicy:
    """
    Domain service for RBAC permission checking logic.
    
    Pure domain logic with no external dependencies.
    """

    @staticmethod
    def has_permission(
        user_permissions: list[Permission], required_permission_code: str
    ) -> bool:
        """
        Check if user has the required permission.
        
        Args:
            user_permissions: List of Permission entities user has
            required_permission_code: The permission code required (e.g., "users:write")
        
        Returns:
            True if user has permission, False otherwise
        """
        permission_codes = {p.code for p in user_permissions}
        return required_permission_code in permission_codes

    @staticmethod
    def has_any_permission(
        user_permissions: list[Permission], required_permission_codes: list[str]
    ) -> bool:
        """Check if user has any of the required permissions."""
        permission_codes = {p.code for p in user_permissions}
        return any(code in permission_codes for code in required_permission_codes)

    @staticmethod
    def has_all_permissions(
        user_permissions: list[Permission], required_permission_codes: list[str]
    ) -> bool:
        """Check if user has all of the required permissions."""
        permission_codes = {p.code for p in user_permissions}
        return all(code in permission_codes for code in required_permission_codes)
