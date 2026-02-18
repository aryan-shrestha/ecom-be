"""SQLAlchemy async session management."""

from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

_engine: Optional[AsyncEngine] = None
_sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None


def init_engine(database_url: str) -> AsyncEngine:
    """Initialize database engine."""
    global _engine, _sessionmaker
    _engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    _sessionmaker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return _engine


def get_engine() -> AsyncEngine:
    """Get database engine."""
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_engine() first.")
    return _engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session (for dependency injection)."""
    if _sessionmaker is None:
        raise RuntimeError("Database engine not initialized. Call init_engine() first.")
    async with _sessionmaker() as session:
        yield session


async def close_engine() -> None:
    """Close database engine."""
    if _engine is not None:
        await _engine.dispose()
