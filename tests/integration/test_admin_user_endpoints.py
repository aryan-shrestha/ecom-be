"""Integration tests for admin user endpoints."""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.sqlalchemy.models.permission_model import PermissionModel
from app.infrastructure.db.sqlalchemy.models.role_model import RoleModel
from app.infrastructure.db.sqlalchemy.models.role_permission_model import RolePermissionModel
from app.infrastructure.db.sqlalchemy.models.user_model import UserModel
from app.infrastructure.db.sqlalchemy.models.user_role_model import UserRoleModel
from app.infrastructure.security.password_hasher import Argon2PasswordHasher


async def _create_admin_with_permission(session: AsyncSession, permission_code: str) -> dict:
    hasher = Argon2PasswordHasher()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    role = RoleModel(id=uuid.uuid4(), name="admin-users")
    perm = PermissionModel(id=uuid.uuid4(), code=permission_code)
    session.add_all([role, perm])
    await session.flush()

    session.add(RolePermissionModel(role_id=role.id, permission_id=perm.id))

    admin_id = uuid.uuid4()
    session.add(
        UserModel(
            id=admin_id,
            email="admin-users@test.com",
            password_hash=hasher.hash_password("Admin123!"),
            is_active=True,
            is_verified=True,
            token_version=0,
            created_at=now,
            updated_at=now,
        )
    )
    await session.flush()
    session.add(UserRoleModel(user_id=admin_id, role_id=role.id))
    await session.commit()

    return {"email": "admin-users@test.com", "password": "Admin123!"}


@pytest.mark.asyncio
async def test_admin_deactivate_user(client: AsyncClient, session: AsyncSession):
    """Admin can deactivate a user via PATCH."""
    admin = await _create_admin_with_permission(session, "users:write")

    # Create target user
    hasher = Argon2PasswordHasher()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    target_user_id = uuid.uuid4()
    session.add(
        UserModel(
            id=target_user_id,
            email="target@test.com",
            password_hash=hasher.hash_password("User123!"),
            is_active=True,
            is_verified=True,
            token_version=0,
            created_at=now,
            updated_at=now,
        )
    )
    await session.commit()

    login = await client.post(
        "/auth/login",
        json={"email": admin["email"], "password": admin["password"]},
    )
    token = login.json()["access_token"]

    resp = await client.patch(
        f"/admin/users/{target_user_id}/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_active"] is False
