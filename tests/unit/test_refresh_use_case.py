"""Unit tests for RefreshUseCase."""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from app.application.dto.auth_dto import RefreshRequest
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.application.ports.crypto_port import TokenHasherPort
from app.application.ports.jwt_port import JwtPort
from app.application.use_cases.auth.refresh import RefreshUseCase
from app.domain.entities.refresh_token import RefreshToken
from app.domain.entities.user import User
from app.domain.errors.domain_errors import (
    RefreshTokenExpiredError,
    RefreshTokenReuseDetectedError,
)
from app.domain.value_objects.email import Email
from tests.conftest import FakeClock


class MockUnitOfWork:
    """Mock Unit of Work for testing."""

    def __init__(self):
        self.users = AsyncMock()
        self.auth = AsyncMock()
        self.refresh_tokens = AsyncMock()
        self.rbac = AsyncMock()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass


@pytest.mark.asyncio
async def test_refresh_success():
    """Test successful token refresh."""
    # Arrange
    user_id = uuid.uuid4()
    family_id = uuid.uuid4()
    now = datetime(2024, 1, 1, 12, 0, 0)

    user = User(
        id=user_id,
        email=Email("user@example.com"),
        password_hash="hash",
        is_active=True,
        is_verified=True,
        token_version=1,
        created_at=now,
        updated_at=now,
    )

    old_token = RefreshToken(
        id=uuid.uuid4(),
        user_id=user_id,
        token_hash="old_token_hash",
        family_id=family_id,
        issued_at=now,
        expires_at=now + timedelta(days=14),
        revoked_at=None,
        replaced_by_token_id=None,
    )

    uow = MockUnitOfWork()
    uow.refresh_tokens.get_by_token_hash.return_value = old_token
    uow.users.get_by_id.return_value = user
    uow.auth.get_user_roles.return_value = ["user"]

    token_hasher = Mock(spec=TokenHasherPort)
    token_hasher.hash_token.side_effect = lambda t: f"{t}_hashed"
    token_hasher.generate_token.return_value = "new_raw_token"

    jwt_service = Mock(spec=JwtPort)
    jwt_service.issue_access_token.return_value = "new_access_token"

    clock = FakeClock(now)
    audit_log = AsyncMock(spec=AuditLogPort)

    use_case = RefreshUseCase(
        uow=uow,
        token_hasher=token_hasher,
        jwt_service=jwt_service,
        clock=clock,
        audit_log=audit_log,
    )

    # Act
    request = RefreshRequest(refresh_token="old_raw_token", csrf_token="csrf")
    response = await use_case.execute(request)

    # Assert
    assert response.access_token == "new_access_token"
    assert response.refresh_token == "new_raw_token"
    assert uow.committed

    # Verify old token was marked as replaced
    uow.refresh_tokens.update.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_token_reuse_detected():
    """Test token reuse detection revokes family and bumps token version."""
    # Arrange
    user_id = uuid.uuid4()
    family_id = uuid.uuid4()
    now = datetime(2024, 1, 1, 12, 0, 0)

    user = User(
        id=user_id,
        email=Email("user@example.com"),
        password_hash="hash",
        is_active=True,
        is_verified=True,
        token_version=1,
        created_at=now,
        updated_at=now,
    )

    # Token that has already been replaced (reuse!)
    old_token = RefreshToken(
        id=uuid.uuid4(),
        user_id=user_id,
        token_hash="old_token_hash",
        family_id=family_id,
        issued_at=now,
        expires_at=now + timedelta(days=14),
        revoked_at=None,
        replaced_by_token_id=uuid.uuid4(),  # Already replaced!
    )

    uow = MockUnitOfWork()
    uow.refresh_tokens.get_by_token_hash.return_value = old_token
    uow.users.get_by_id.return_value = user

    token_hasher = Mock(spec=TokenHasherPort)
    token_hasher.hash_token.return_value = "old_token_hash"

    jwt_service = Mock(spec=JwtPort)
    clock = FakeClock(now)
    audit_log = AsyncMock(spec=AuditLogPort)

    use_case = RefreshUseCase(
        uow=uow,
        token_hasher=token_hasher,
        jwt_service=jwt_service,
        clock=clock,
        audit_log=audit_log,
    )

    # Act & Assert
    with pytest.raises(RefreshTokenReuseDetectedError):
        request = RefreshRequest(refresh_token="old_raw_token", csrf_token="csrf")
        await use_case.execute(request)

    # Verify family was revoked
    uow.refresh_tokens.revoke_family.assert_called_once_with(family_id, now)

    # Verify token version was bumped
    uow.users.update.assert_called_once()
    updated_user = uow.users.update.call_args[0][0]
    assert updated_user.token_version == 2


@pytest.mark.asyncio
async def test_refresh_expired_token():
    """Test refreshing expired token fails."""
    # Arrange
    user_id = uuid.uuid4()
    now = datetime(2024, 1, 1, 12, 0, 0)

    # Expired token
    old_token = RefreshToken(
        id=uuid.uuid4(),
        user_id=user_id,
        token_hash="old_token_hash",
        family_id=uuid.uuid4(),
        issued_at=now - timedelta(days=15),
        expires_at=now - timedelta(days=1),  # Expired yesterday
        revoked_at=None,
        replaced_by_token_id=None,
    )

    uow = MockUnitOfWork()
    uow.refresh_tokens.get_by_token_hash.return_value = old_token

    token_hasher = Mock(spec=TokenHasherPort)
    token_hasher.hash_token.return_value = "old_token_hash"

    jwt_service = Mock(spec=JwtPort)
    clock = FakeClock(now)
    audit_log = AsyncMock(spec=AuditLogPort)

    use_case = RefreshUseCase(
        uow=uow,
        token_hasher=token_hasher,
        jwt_service=jwt_service,
        clock=clock,
        audit_log=audit_log,
    )

    # Act & Assert
    with pytest.raises(RefreshTokenExpiredError):
        request = RefreshRequest(refresh_token="old_raw_token", csrf_token="csrf")
        await use_case.execute(request)
