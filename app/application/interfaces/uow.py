"""Unit of Work interface for transaction management."""

from abc import ABC, abstractmethod
from typing import Any

from app.domain.repositories.auth_repository import AuthRepository
from app.domain.repositories.rbac_repository import RbacRepository
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.repositories.product_repository import ProductRepository
from app.domain.repositories.category_repository import CategoryRepository
from app.domain.repositories.inventory_repository import InventoryRepository


class UnitOfWork(ABC):
    """
    Unit of Work interface for transactional operations.
    
    Provides access to repositories within a transaction boundary.
    """

    users: UserRepository
    auth: AuthRepository
    refresh_tokens: RefreshTokenRepository
    rbac: RbacRepository
    products: ProductRepository
    categories: CategoryRepository
    inventory: InventoryRepository

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        """Enter transaction context."""
        ...

    @abstractmethod
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit transaction context (commit or rollback)."""
        ...

    @abstractmethod
    async def commit(self) -> None:
        """Commit transaction."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback transaction."""
        ...
