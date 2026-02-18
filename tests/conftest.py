"""Test configuration and fixtures."""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.application.ports.clock_port import ClockPort
from app.infrastructure.db.sqlalchemy.base import Base
from app.infrastructure.db.sqlalchemy.session import get_session
from app.presentation.api.main import app

# Test database URL (use a separate test database)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/ecom_auth_test"


class FakeClock(ClockPort):
    """Fake clock for deterministic testing."""

    def __init__(self, fixed_time: datetime) -> None:
        self._time = fixed_time

    def now(self) -> datetime:
        """Return fixed time."""
        return self._time

    def advance(self, **kwargs) -> None:
        """Advance time."""
        from datetime import timedelta
        self._time += timedelta(**kwargs)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async with sessionmaker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def fake_clock() -> FakeClock:
    """Create fake clock for testing."""
    return FakeClock(datetime(2024, 1, 1, 12, 0, 0))
