"""Integration tests for order (checkout + history) endpoints."""

import uuid
import datetime as _dt

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.sqlalchemy.models.inventory_model import InventoryModel
from app.infrastructure.db.sqlalchemy.models.permission_model import PermissionModel
from app.infrastructure.db.sqlalchemy.models.product_model import ProductModel
from app.infrastructure.db.sqlalchemy.models.product_variant_model import ProductVariantModel
from app.infrastructure.db.sqlalchemy.models.role_model import RoleModel
from app.infrastructure.db.sqlalchemy.models.role_permission_model import RolePermissionModel
from app.infrastructure.db.sqlalchemy.models.user_role_model import UserRoleModel


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def _create_published_variant(
    session: AsyncSession,
    on_hand: int = 50,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Seed a PUBLISHED product + ACTIVE variant + inventory row."""
    product_id = uuid.uuid4()
    variant_id = uuid.uuid4()

    product = ProductModel(
        id=product_id,
        status="PUBLISHED",
        name="Order Test Widget",
        slug=f"order-widget-{product_id.hex[:8]}",
        description_short=None,
        description_long=None,
        tags=[],
        featured=False,
        sort_order=0,
        created_at=_dt.datetime.utcnow(),
        updated_at=_dt.datetime.utcnow(),
    )
    variant = ProductVariantModel(
        id=variant_id,
        product_id=product_id,
        sku=f"SKU-ORD-{variant_id.hex[:8]}",
        status="ACTIVE",
        price_amount=1500,  # $15.00
        price_currency="USD",
        is_default=True,
        created_at=_dt.datetime.utcnow(),
        updated_at=_dt.datetime.utcnow(),
    )
    inventory = InventoryModel(
        variant_id=variant_id,
        on_hand=on_hand,
        reserved=0,
        allow_backorder=False,
    )

    session.add(product)
    session.add(variant)
    session.add(inventory)
    await session.commit()
    return product_id, variant_id


async def _register_and_login(client: AsyncClient, email: str, password: str = "SecurePass123") -> tuple[str, uuid.UUID]:
    """Register a user, login, and return (access_token, user_id)."""
    reg = await client.post("/auth/register", json={"email": email, "password": password})
    user_id = uuid.UUID(reg.json()["user_id"])
    login = await client.post("/auth/login", json={"email": email, "password": password})
    return login.json()["access_token"], user_id


async def _grant_permission(session: AsyncSession, user_id: uuid.UUID, permission_code: str) -> None:
    """Create role+permission and assign to user."""
    role_id = uuid.uuid4()
    perm_id = uuid.uuid4()
    session.add(RoleModel(id=role_id, name=f"role-{role_id.hex[:6]}"))
    session.add(PermissionModel(id=perm_id, code=permission_code))
    session.add(RolePermissionModel(role_id=role_id, permission_id=perm_id))
    session.add(UserRoleModel(user_id=user_id, role_id=role_id))
    await session.commit()


async def _add_item_and_checkout(
    client: AsyncClient,
    token: str,
    variant_id: uuid.UUID,
    quantity: int = 2,
    idempotency_key: str | None = None,
) -> dict:
    """End-to-end helper: add item to auth cart then checkout. Returns order JSON."""
    if idempotency_key is None:
        idempotency_key = str(uuid.uuid4())

    # Add to cart
    await client.post(
        "/cart/items",
        json={"variant_id": str(variant_id), "quantity": quantity},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Checkout
    resp = await client.post(
        "/checkout",
        json={"shipping_address": "123 Main St", "notes": None},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
        },
    )
    return resp


# ---------------------------------------------------------------------------
# Checkout tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_checkout_creates_order(client: AsyncClient, session: AsyncSession):
    """Successful checkout creates an order with PENDING_PAYMENT status."""
    _, variant_id = await _create_published_variant(session)
    token, _ = await _register_and_login(client, f"checkout_{uuid.uuid4().hex[:6]}@test.com")

    resp = await _add_item_and_checkout(client, token, variant_id, quantity=2)

    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "PENDING_PAYMENT"
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["unit_price_amount"] == 1500
    assert data["items"][0]["line_total_amount"] == 3000
    assert data["subtotal_amount"] == 3000
    assert data["grand_total_amount"] == 3000
    assert data["order_number"].startswith("ORD-")


@pytest.mark.asyncio
async def test_checkout_reserves_inventory(client: AsyncClient, session: AsyncSession):
    """After checkout the inventory row has reserved incremented."""
    _, variant_id = await _create_published_variant(session, on_hand=50)
    token, _ = await _register_and_login(client, f"inv_{uuid.uuid4().hex[:6]}@test.com")

    await _add_item_and_checkout(client, token, variant_id, quantity=3)

    result = await session.execute(
        select(InventoryModel).where(InventoryModel.variant_id == variant_id)
    )
    inv = result.scalar_one()
    assert inv.reserved == 3


@pytest.mark.asyncio
async def test_checkout_requires_idempotency_key(client: AsyncClient, session: AsyncSession):
    """POST /checkout without Idempotency-Key header returns 400."""
    _, variant_id = await _create_published_variant(session)
    token, _ = await _register_and_login(client, f"nokey_{uuid.uuid4().hex[:6]}@test.com")

    await client.post(
        "/cart/items",
        json={"variant_id": str(variant_id), "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.post(
        "/checkout",
        json={"shipping_address": "42 Elm St"},
        headers={"Authorization": f"Bearer {token}"},
        # intentionally omit Idempotency-Key
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_checkout_empty_cart_returns_error(client: AsyncClient, session: AsyncSession):
    """Checkout with an empty cart returns 422."""
    token, _ = await _register_and_login(client, f"empty_{uuid.uuid4().hex[:6]}@test.com")

    # Ensure we have a cart (no items)
    await client.get("/cart", headers={"Authorization": f"Bearer {token}"})

    resp = await client.post(
        "/checkout",
        json={"shipping_address": "99 Nowhere Rd"},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": str(uuid.uuid4()),
        },
    )
    # Empty cart → domain error → 422
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_checkout_idempotency_returns_same_order(client: AsyncClient, session: AsyncSession):
    """Two POST /checkout calls with the same Idempotency-Key return the same order."""
    _, variant_id = await _create_published_variant(session)
    token, _ = await _register_and_login(client, f"idem_{uuid.uuid4().hex[:6]}@test.com")
    idempotency_key = str(uuid.uuid4())

    # First call
    resp1 = await _add_item_and_checkout(client, token, variant_id, quantity=1, idempotency_key=idempotency_key)
    assert resp1.status_code == 201
    order_id_first = resp1.json()["id"]

    # Second call with the SAME idempotency key — should get back the cached response
    # (the cart is now converted so this tests the idempotency cache path)
    resp2 = await client.post(
        "/checkout",
        json={"shipping_address": "123 Main St"},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
        },
    )
    # Should succeed (200 or 201) and return identical order
    assert resp2.status_code in (200, 201)
    assert resp2.json()["id"] == order_id_first


# ---------------------------------------------------------------------------
# Customer order history tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_my_orders(client: AsyncClient, session: AsyncSession):
    """GET /orders returns the authenticated user's orders."""
    _, variant_id = await _create_published_variant(session)
    token, _ = await _register_and_login(client, f"listord_{uuid.uuid4().hex[:6]}@test.com")

    await _add_item_and_checkout(client, token, variant_id, quantity=1)

    resp = await client.get("/orders", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["orders"]) >= 1


@pytest.mark.asyncio
async def test_list_orders_requires_auth(client: AsyncClient):
    """GET /orders without auth returns 401."""
    resp = await client.get("/orders")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_order_detail(client: AsyncClient, session: AsyncSession):
    """GET /orders/{id} returns order details for the owner."""
    _, variant_id = await _create_published_variant(session)
    token, _ = await _register_and_login(client, f"detail_{uuid.uuid4().hex[:6]}@test.com")

    checkout_resp = await _add_item_and_checkout(client, token, variant_id, quantity=2)
    order_id = checkout_resp.json()["id"]

    resp = await client.get(f"/orders/{order_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == order_id


@pytest.mark.asyncio
async def test_get_order_detail_wrong_user_returns_403(client: AsyncClient, session: AsyncSession):
    """User B cannot access User A's order."""
    _, variant_id = await _create_published_variant(session)

    # User A creates order
    token_a, _ = await _register_and_login(client, f"usera_{uuid.uuid4().hex[:6]}@test.com")
    checkout_resp = await _add_item_and_checkout(client, token_a, variant_id, quantity=1)
    order_id = checkout_resp.json()["id"]

    # User B tries to access it
    token_b, _ = await _register_and_login(client, f"userb_{uuid.uuid4().hex[:6]}@test.com")
    resp = await client.get(f"/orders/{order_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Admin order tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_admin_list_orders_requires_permission(client: AsyncClient, session: AsyncSession):
    """GET /admin/orders without orders:manage permission returns 403."""
    token, _ = await _register_and_login(client, f"noadmin_{uuid.uuid4().hex[:6]}@test.com")

    resp = await client.get("/admin/orders", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_list_orders_requires_auth(client: AsyncClient):
    """GET /admin/orders without auth returns 401."""
    resp = await client.get("/admin/orders")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_list_orders_with_permission(client: AsyncClient, session: AsyncSession):
    """Admin with orders:manage can list all orders."""
    _, variant_id = await _create_published_variant(session)

    # Customer creates an order
    cust_token, _ = await _register_and_login(client, f"cust_{uuid.uuid4().hex[:6]}@test.com")
    await _add_item_and_checkout(client, cust_token, variant_id, quantity=1)

    # Admin user
    admin_token, admin_id = await _register_and_login(client, f"admn_{uuid.uuid4().hex[:6]}@test.com")
    await _grant_permission(session, admin_id, "orders:manage")

    resp = await client.get("/admin/orders", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_admin_get_order(client: AsyncClient, session: AsyncSession):
    """Admin can retrieve any order by ID."""
    _, variant_id = await _create_published_variant(session)

    cust_token, _ = await _register_and_login(client, f"cust2_{uuid.uuid4().hex[:6]}@test.com")
    checkout_resp = await _add_item_and_checkout(client, cust_token, variant_id, quantity=1)
    order_id = checkout_resp.json()["id"]

    admin_token, admin_id = await _register_and_login(client, f"admn2_{uuid.uuid4().hex[:6]}@test.com")
    await _grant_permission(session, admin_id, "orders:manage")

    resp = await client.get(f"/admin/orders/{order_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == order_id


@pytest.mark.asyncio
async def test_admin_cancel_order(client: AsyncClient, session: AsyncSession):
    """Admin can cancel a PENDING_PAYMENT order; inventory is released."""
    _, variant_id = await _create_published_variant(session, on_hand=20)

    cust_token, _ = await _register_and_login(client, f"cust3_{uuid.uuid4().hex[:6]}@test.com")
    checkout_resp = await _add_item_and_checkout(client, cust_token, variant_id, quantity=4)
    order_id = checkout_resp.json()["id"]

    # Confirm inventory was reserved
    inv_before = await session.execute(
        select(InventoryModel).where(InventoryModel.variant_id == variant_id)
    )
    assert inv_before.scalar_one().reserved == 4

    admin_token, admin_id = await _register_and_login(client, f"admn3_{uuid.uuid4().hex[:6]}@test.com")
    await _grant_permission(session, admin_id, "orders:manage")

    cancel_resp = await client.post(
        f"/admin/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELED"

    # Expire and re-fetch inventory to see the release
    await session.expire_all()
    inv_after = await session.execute(
        select(InventoryModel).where(InventoryModel.variant_id == variant_id)
    )
    assert inv_after.scalar_one().reserved == 0


@pytest.mark.asyncio
async def test_admin_cancel_order_not_found(client: AsyncClient, session: AsyncSession):
    """Admin cancel on non-existent order returns 404."""
    admin_token, admin_id = await _register_and_login(client, f"admn4_{uuid.uuid4().hex[:6]}@test.com")
    await _grant_permission(session, admin_id, "orders:manage")

    resp = await client.post(
        f"/admin/orders/{uuid.uuid4()}/cancel",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404
