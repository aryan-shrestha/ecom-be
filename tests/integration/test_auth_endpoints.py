"""Integration tests for authentication endpoints."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.infrastructure.db.sqlalchemy.models.permission_model import PermissionModel
from app.infrastructure.db.sqlalchemy.models.role_model import RoleModel
from app.infrastructure.db.sqlalchemy.models.role_permission_model import RolePermissionModel
from app.infrastructure.db.sqlalchemy.models.user_model import UserModel
from app.infrastructure.db.sqlalchemy.models.user_role_model import UserRoleModel


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Test successful user registration."""
    response = await client.post(
        "/auth/register",
        json={"email": "newuser@example.com", "password": "SecurePass123"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "user_id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with duplicate email fails."""
    # Register first user
    await client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "SecurePass123"},
    )

    # Try to register again with same email
    response = await client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "SecurePass123"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login returns access token and sets cookies."""
    # Register user
    await client.post(
        "/auth/register",
        json={"email": "loginuser@example.com", "password": "SecurePass123"},
    )

    # Login
    response = await client.post(
        "/auth/login",
        json={"email": "loginuser@example.com", "password": "SecurePass123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"

    # Check cookies
    assert "refresh_token" in response.cookies
    assert "csrf_token" in response.cookies


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials fails."""
    # Register user
    await client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "SecurePass123"},
    )

    # Try to login with wrong password
    response = await client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "WrongPassword"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient):
    """Test refresh token rotation."""
    # Register and login
    await client.post(
        "/auth/register",
        json={"email": "refresh@example.com", "password": "SecurePass123"},
    )

    login_response = await client.post(
        "/auth/login",
        json={"email": "refresh@example.com", "password": "SecurePass123"},
    )

    old_refresh_token = login_response.cookies["refresh_token"]
    csrf_token = login_response.cookies["csrf_token"]

    # Refresh
    refresh_response = await client.post(
        "/auth/refresh",
        cookies={"refresh_token": old_refresh_token, "csrf_token": csrf_token},
        headers={"X-CSRF-Token": csrf_token},
    )

    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "access_token" in data

    new_refresh_token = refresh_response.cookies["refresh_token"]
    assert new_refresh_token != old_refresh_token

    # Try to use old refresh token again (should fail - reuse detection)
    reuse_response = await client.post(
        "/auth/refresh",
        cookies={"refresh_token": old_refresh_token, "csrf_token": csrf_token},
        headers={"X-CSRF-Token": csrf_token},
    )

    assert reuse_response.status_code == 401
    assert "reuse" in reuse_response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    """Test getting current user info."""
    # Register and login
    await client.post(
        "/auth/register",
        json={"email": "me@example.com", "password": "SecurePass123"},
    )

    login_response = await client.post(
        "/auth/login",
        json={"email": "me@example.com", "password": "SecurePass123"},
    )

    access_token = login_response.json()["access_token"]

    # Get me
    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    """Test logout revokes refresh token."""
    # Register and login
    await client.post(
        "/auth/register",
        json={"email": "logout@example.com", "password": "SecurePass123"},
    )

    login_response = await client.post(
        "/auth/login",
        json={"email": "logout@example.com", "password": "SecurePass123"},
    )

    refresh_token = login_response.cookies["refresh_token"]
    csrf_token = login_response.cookies["csrf_token"]

    # Logout
    response = await client.post(
        "/auth/logout",
        cookies={"refresh_token": refresh_token, "csrf_token": csrf_token},
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 200

    # Try to refresh with logged-out token (should fail)
    refresh_response = await client.post(
        "/auth/refresh",
        cookies={"refresh_token": refresh_token, "csrf_token": csrf_token},
        headers={"X-CSRF-Token": csrf_token},
    )

    assert refresh_response.status_code == 401


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient):
    """Test password change revokes all sessions."""
    # Register and login
    await client.post(
        "/auth/register",
        json={"email": "changepw@example.com", "password": "SecurePass123"},
    )

    login_response = await client.post(
        "/auth/login",
        json={"email": "changepw@example.com", "password": "SecurePass123"},
    )

    old_access_token = login_response.json()["access_token"]

    # Change password
    response = await client.post(
        "/auth/change-password",
        json={"old_password": "SecurePass123", "new_password": "NewSecure456"},
        headers={"Authorization": f"Bearer {old_access_token}"},
    )

    assert response.status_code == 200

    # Old access token should be invalid (token version bumped)
    me_response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {old_access_token}"},
    )

    assert me_response.status_code == 401

    # New login should work
    new_login_response = await client.post(
        "/auth/login",
        json={"email": "changepw@example.com", "password": "NewSecure456"},
    )

    assert new_login_response.status_code == 200
