"""SQLAlchemy Unit of Work implementation."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.uow import UnitOfWork
from app.infrastructure.repositories.sqlalchemy.auth_repo import SqlAlchemyAuthRepository
from app.infrastructure.repositories.sqlalchemy.rbac_repo import SqlAlchemyRbacRepository
from app.infrastructure.repositories.sqlalchemy.refresh_token_repo import (
    SqlAlchemyRefreshTokenRepository,
)
from app.infrastructure.repositories.sqlalchemy.user_repo import SqlAlchemyUserRepository
from app.infrastructure.repositories.sqlalchemy.product_repo import SqlAlchemyProductRepository
from app.infrastructure.repositories.sqlalchemy.category_repo import SqlAlchemyCategoryRepository
from app.infrastructure.repositories.sqlalchemy.inventory_repo import SqlAlchemyInventoryRepository


class SqlAlchemyUnitOfWork(UnitOfWork):
    """SQLAlchemy Unit of Work for transaction management."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.users = SqlAlchemyUserRepository(session)
        self.auth = SqlAlchemyAuthRepository(session)
        self.refresh_tokens = SqlAlchemyRefreshTokenRepository(session)
        self.rbac = SqlAlchemyRbacRepository(session)
        self.products = SqlAlchemyProductRepository(session)
        self.categories = SqlAlchemyCategoryRepository(session)
        self.inventory = SqlAlchemyInventoryRepository(session)

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        """Enter transaction context."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit transaction context (commit or rollback)."""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self) -> None:
        """Commit transaction."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback transaction."""
        await self._session.rollback()
