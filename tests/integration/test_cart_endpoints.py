"""Integration tests for cart endpoints."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.sqlalchemy.models.inventory_model import InventoryModel
from app.infrastructure.db.sqlalchemy.models.product_model import ProductModel
from app.infrastructure.db.sqlalchemy.models.product_variant_model import ProductVariantModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _register_and_login(client: AsyncClient, email: str, password: str = "SecurePass123") -> str:
    await client.post("/auth/register", json={"email": email, "password": password})
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


async def _create_published_variant(session: AsyncSession) -> tuple[uuid.UUID, uuid.UUID]:
    """Create a published product with one active variant and inventory. Returns (product_id, variant_id)."""
    product_id = uuid.uuid4()
    variant_id = uuid.uuid4()

    product = ProductModel(
        id=product_id,
        status="PUBLISHED",
        name="Test Widget",
        slug=f"test-widget-{product_id.hex[:8]}",
        description_short=None,
        description_long=None,
        tags=[],
        featured=False,
        sort_order=0,
        created_at=__import__("datetime").datetime.utcnow(),
        updated_at=__import__("datetime").datetime.utcnow(),
    )
    variant = ProductVariantModel(
        id=variant_id,
        product_id=product_id,
        sku=f"SKU-{variant_id.hex[:8]}",
        status="ACTIVE",
        price_amount=2000,  # $20.00
        price_currency="USD",
        is_default=True,
        created_at=__import__("datetime").datetime.utcnow(),
        updated_at=__import__("datetime").datetime.utcnow(),
    )
    inventory = InventoryModel(
        variant_id=variant_id,
        on_hand=100,
        reserved=0,
        allow_backorder=False,
    )

    session.add(product)
    session.add(variant)
    session.add(inventory)
    await session.commit()
    return product_id, variant_id


# ---------------------------------------------------------------------------
# Guest cart tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_cart_creates_guest_cart(client: AsyncClient):
    """GET /cart without any token creates a new guest cart and sets cookie."""
    resp = await client.get("/cart")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ACTIVE"
    assert data["items"] == []
    # Cookie should be set
    assert "cart_token" in resp.cookies


@pytest.mark.asyncio
async def test_add_item_to_guest_cart(client: AsyncClient, session: AsyncSession):
    """Guest can add an item to their cart."""
    _, variant_id = await _create_published_variant(session)

    # Get cart (creates guest token)
    cart_resp = await client.get("/cart")
    cart_token = cart_resp.cookies.get("cart_token")

    resp = await client.post(
        "/cart/items",
        json={"variant_id": str(variant_id), "quantity": 2},
        cookies={"cart_token": cart_token} if cart_token else {},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["unit_price_amount"] == 2000
    assert data["items"][0]["line_subtotal_amount"] == 4000
    assert data["subtotal_amount"] == 4000


@pytest.mark.asyncio
async def test_update_cart_item_quantity(client: AsyncClient, session: AsyncSession):
    """Guest can update cart item quantity."""
    _, variant_id = await _create_published_variant(session)

    cart_resp = await client.get("/cart")
    cart_token = cart_resp.cookies.get("cart_token")
    cookies = {"cart_token": cart_token} if cart_token else {}

    # Add item
    add_resp = await client.post(
        "/cart/items",
        json={"variant_id": str(variant_id), "quantity": 1},
        cookies=cookies,
    )
    item_id = add_resp.json()["items"][0]["id"]

    # Update
    update_resp = await client.patch(
        f"/cart/items/{item_id}",
        json={"quantity": 5},
        cookies=cookies,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["items"][0]["quantity"] == 5


@pytest.mark.asyncio
async def test_remove_cart_item(client: AsyncClient, session: AsyncSession):
    """Guest can remove a cart item."""
    _, variant_id = await _create_published_variant(session)

    cart_resp = await client.get("/cart")
    cart_token = cart_resp.cookies.get("cart_token")
    cookies = {"cart_token": cart_token} if cart_token else {}

    add_resp = await client.post(
        "/cart/items",
        json={"variant_id": str(variant_id), "quantity": 3},
        cookies=cookies,
    )
    item_id = add_resp.json()["items"][0]["id"]

    del_resp = await client.delete(f"/cart/items/{item_id}", cookies=cookies)
    assert del_resp.status_code == 200
    assert del_resp.json()["items"] == []


@pytest.mark.asyncio
async def test_clear_cart(client: AsyncClient, session: AsyncSession):
    """POST /cart/clear removes all items."""
    _, variant_id = await _create_published_variant(session)

    cart_resp = await client.get("/cart")
    cart_token = cart_resp.cookies.get("cart_token")
    cookies = {"cart_token": cart_token} if cart_token else {}

    await client.post(
        "/cart/items",
        json={"variant_id": str(variant_id), "quantity": 2},
        cookies=cookies,
    )

    clear_resp = await client.post("/cart/clear", cookies=cookies)
    assert clear_resp.status_code == 200
    assert clear_resp.json()["items"] == []


# ---------------------------------------------------------------------------
# Authenticated cart tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authenticated_user_has_own_cart(client: AsyncClient, session: AsyncSession):
    """Authenticated users have their own user-linked cart."""
    _, variant_id = await _create_published_variant(session)
    token = await _register_and_login(client, f"cartuser_{uuid.uuid4().hex[:6]}@test.com")

    resp = await client.post(
        "/cart/items",
        json={"variant_id": str(variant_id), "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["user_id"] is not None


@pytest.mark.asyncio
async def test_add_inactive_variant_is_rejected(client: AsyncClient, session: AsyncSession):
    """Adding an INACTIVE variant raises 422."""
    product_id = uuid.uuid4()
    variant_id = uuid.uuid4()
    import datetime as _dt

    product = ProductModel(
        id=product_id, status="PUBLISHED", name="Widget2",
        slug=f"widget2-{product_id.hex[:8]}",
        description_short=None, description_long=None,
        tags=[], featured=False, sort_order=0,
        created_at=_dt.datetime.utcnow(), updated_at=_dt.datetime.utcnow(),
    )
    variant = ProductVariantModel(
        id=variant_id, product_id=product_id,
        sku=f"SKU-INACTIVE-{variant_id.hex[:8]}",
        status="INACTIVE",
        price_amount=1000, price_currency="USD",
        is_default=True,
        created_at=_dt.datetime.utcnow(), updated_at=_dt.datetime.utcnow(),
    )
    session.add(product)
    session.add(variant)
    await session.commit()

    cart_resp = await client.get("/cart")
    cookies = {"cart_token": cart_resp.cookies.get("cart_token")} if cart_resp.cookies.get("cart_token") else {}

    resp = await client.post(
        "/cart/items",
        json={"variant_id": str(variant_id), "quantity": 1},
        cookies=cookies,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_add_archived_product_variant_is_rejected(client: AsyncClient, session: AsyncSession):
    """Adding a variant of an ARCHIVED product raises 422."""
    product_id = uuid.uuid4()
    variant_id = uuid.uuid4()
    import datetime as _dt

    product = ProductModel(
        id=product_id, status="ARCHIVED", name="OldWidget",
        slug=f"old-widget-{product_id.hex[:8]}",
        description_short=None, description_long=None,
        tags=[], featured=False, sort_order=0,
        created_at=_dt.datetime.utcnow(), updated_at=_dt.datetime.utcnow(),
    )
    variant = ProductVariantModel(
        id=variant_id, product_id=product_id,
        sku=f"SKU-ARCH-{variant_id.hex[:8]}",
        status="ACTIVE",
        price_amount=1500, price_currency="USD",
        is_default=True,
        created_at=_dt.datetime.utcnow(), updated_at=_dt.datetime.utcnow(),
    )
    inventory = InventoryModel(variant_id=variant_id, on_hand=50, reserved=0, allow_backorder=False)
    session.add(product)
    session.add(variant)
    session.add(inventory)
    await session.commit()

    cart_resp = await client.get("/cart")
    cookies = {"cart_token": cart_resp.cookies.get("cart_token")} if cart_resp.cookies.get("cart_token") else {}

    resp = await client.post(
        "/cart/items",
        json={"variant_id": str(variant_id), "quantity": 1},
        cookies=cookies,
    )
    assert resp.status_code == 422
