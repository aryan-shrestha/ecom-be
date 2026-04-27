"""Integration tests for seeded admin permissions."""

import pytest
from httpx import AsyncClient

from config.settings import settings
from scripts.seed_data import seed_data
from tests.conftest import TEST_DATABASE_URL


@pytest.mark.asyncio
async def test_seeded_admin_has_orders_and_rbac_permissions(client: AsyncClient):
    """Seeded admin can access admin orders and RBAC endpoints."""
    settings.database_url = TEST_DATABASE_URL

    await seed_data()

    login_response = await client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"},
    )
    token = login_response.json()["access_token"]

    orders_response = await client.get(
        "/admin/orders",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert orders_response.status_code == 200

    roles_response = await client.get(
        "/rbac/roles",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert roles_response.status_code == 200
