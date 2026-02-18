"""Check permission use case for RBAC."""

from uuid import UUID

from app.application.interfaces.uow import UnitOfWork
from app.application.ports.cache_port import CachePort
from app.domain.entities.permission import Permission
from app.domain.errors.domain_errors import InsufficientPermissionsError
from app.domain.policies.rbac_policy import RbacPolicy


class CheckPermissionUseCase:
    """Use case for checking if user has required permission."""

    def __init__(
        self,
        uow: UnitOfWork,
        cache: CachePort,
        cache_ttl_seconds: int = 300,  # 5 minutes
    ) -> None:
        self.uow = uow
        self.cache = cache
        self.cache_ttl_seconds = cache_ttl_seconds

    async def execute(
        self, user_id: UUID, roles: list[str], required_permission: str
    ) -> None:
        """
        Check if user has required permission.
        
        Raises:
            InsufficientPermissionsError: If user lacks permission
        """
        # Get permissions for roles (with caching)
        permissions = await self._get_permissions_for_roles(roles)

        # Check permission using domain policy
        if not RbacPolicy.has_permission(permissions, required_permission):
            raise InsufficientPermissionsError(
                f"User {user_id} lacks permission: {required_permission}"
            )

    async def _get_permissions_for_roles(self, roles: list[str]) -> list[Permission]:
        """Get permissions for roles, with caching."""
        if not roles:
            return []

        # Create cache key from sorted roles
        cache_key = f"permissions:{':'.join(sorted(roles))}"

        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Cache miss - query database
        async with self.uow:
            permissions = await self.uow.rbac.get_permissions_for_roles(roles)

        # Cache for future requests
        await self.cache.set(cache_key, permissions, self.cache_ttl_seconds)

        return permissions
