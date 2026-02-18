"""Integration tests for RBAC endpoints."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.sqlalchemy.models.permission_model import PermissionModel
from app.infrastructure.db.sqlalchemy.models.role_model import RoleModel
from app.infrastructure.db.sqlalchemy.models.role_permission_model import RolePermissionModel


async def create_role_with_permission(
    session: AsyncSession, role_name: str, permission_code: str
) -> tuple[uuid.UUID, uuid.UUID]:
    """Helper to create role with permission."""
    role_id = uuid.uuid4()
    permission_id = uuid.uuid4()

    role = RoleModel(id=role_id, name=role_name)
    permission = PermissionModel(id=permission_id, code=permission_code)
    role_permission = RolePermissionModel(role_id=role_id, permission_id=permission_id)

    session.add(role)
    session.add(permission)
    session.add(role_permission)
    await session.commit()

    return role_id, permission_id


@pytest.mark.asyncio
async def test_assign_role_requires_permission(client: AsyncClient, session: AsyncSession):
    """Test that assigning role requires rbac:assign permission."""
    # Create role and permission
    await create_role_with_permission(session, "admin", "rbac:assign")

    # Register user without admin role
    await client.post(
        "/auth/register",
        json={"email": "normaluser@example.com", "password": "SecurePass123"},
    )

    login_response = await client.post(
        "/auth/login",
        json={"email": "normaluser@example.com", "password": "SecurePass123"},
    )

    access_token = login_response.json()["access_token"]

    # Try to assign role (should fail - no permission)
    response = await client.post(
        "/rbac/assign-role",
        json={"user_id": str(uuid.uuid4()), "role_name": "admin"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_permission_checking_works(client: AsyncClient, session: AsyncSession):
    """Test that permission checking correctly allows/denies access."""
    # Create admin role with rbac:assign permission
    await create_role_with_permission(session, "admin", "rbac:assign")

    # Register user
    register_response = await client.post(
        "/auth/register",
        json={"email": "admin@example.com", "password": "SecurePass123"},
    )

    user_id = uuid.UUID(register_response.json()["user_id"])

    # Manually assign admin role to user
    from app.infrastructure.db.sqlalchemy.models.user_role_model import UserRoleModel
    from sqlalchemy import select

    stmt = select(RoleModel).where(RoleModel.name == "admin")
    result = await session.execute(stmt)
    role = result.scalar_one()

    user_role = UserRoleModel(user_id=user_id, role_id=role.id)
    session.add(user_role)
    await session.commit()

    # Login
    login_response = await client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "SecurePass123"},
    )

    access_token = login_response.json()["access_token"]

    # Create another user to assign role to
    other_user_response = await client.post(
        "/auth/register",
        json={"email": "otheruser@example.com", "password": "SecurePass123"},
    )

    other_user_id = other_user_response.json()["user_id"]

    # Now assign role should work
    response = await client.post(
        "/rbac/assign-role",
        json={"user_id": other_user_id, "role_name": "admin"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
