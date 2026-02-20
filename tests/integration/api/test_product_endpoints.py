"""Integration tests for product endpoints."""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.sqlalchemy.models.user_model import UserModel
from app.infrastructure.db.sqlalchemy.models.role_model import RoleModel
from app.infrastructure.db.sqlalchemy.models.permission_model import PermissionModel
from app.infrastructure.db.sqlalchemy.models.user_role_model import UserRoleModel
from app.infrastructure.db.sqlalchemy.models.role_permission_model import RolePermissionModel
from app.infrastructure.security.password_hasher import Argon2PasswordHasher


@pytest.fixture
async def admin_user_with_permissions(session: AsyncSession) -> dict:
    """Create admin user with product management permissions."""
    hasher = Argon2PasswordHasher()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Create admin role
    admin_role = RoleModel(id=uuid.uuid4(), name="admin")
    session.add(admin_role)

    # Create all product permissions
    permissions = [
        PermissionModel(id=uuid.uuid4(), code="products:read"),
        PermissionModel(id=uuid.uuid4(), code="products:write"),
        PermissionModel(id=uuid.uuid4(), code="products:publish"),
        PermissionModel(id=uuid.uuid4(), code="products:archive"),
        PermissionModel(id=uuid.uuid4(), code="products:variant_write"),
        PermissionModel(id=uuid.uuid4(), code="categories:read"),
        PermissionModel(id=uuid.uuid4(), code="categories:write"),
        PermissionModel(id=uuid.uuid4(), code="inventory:read"),
        PermissionModel(id=uuid.uuid4(), code="inventory:adjust"),
        PermissionModel(id=uuid.uuid4(), code="products:media_write"),
    ]
    session.add_all(permissions)
    await session.flush()

    # Assign permissions to admin role
    for perm in permissions:
        role_perm = RolePermissionModel(role_id=admin_role.id, permission_id=perm.id)
        session.add(role_perm)

    # Create admin user
    admin_user_id = uuid.uuid4()
    admin_user = UserModel(
        id=admin_user_id,
        email="admin@test.com",
        password_hash=hasher.hash_password("Admin123!"),
        is_active=True,
        is_verified=True,
        token_version=0,
        created_at=now,
        updated_at=now,
    )
    session.add(admin_user)
    await session.flush()

    # Assign role to user
    user_role = UserRoleModel(user_id=admin_user_id, role_id=admin_role.id)
    session.add(user_role)

    await session.commit()

    return {"email": "admin@test.com", "password": "Admin123!"}


@pytest.fixture
async def auth_headers(client: AsyncClient, admin_user_with_permissions: dict) -> dict:
    """Get authentication headers for admin user."""
    login_response = await client.post(
        "/auth/login",
        json={
            "email": admin_user_with_permissions["email"],
            "password": admin_user_with_permissions["password"],
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_product_success(client: AsyncClient, auth_headers: dict):
    """Test creating a product successfully."""
    response = await client.post(
        "/admin/products",
        json={
            "name": "Test Product",
            "slug": "test-product",
            "description_short": "A test product",
            "description_long": "This is a longer description",
            "tags": ["electronics", "gadgets"],
            "featured": False,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["slug"] == "test-product"
    assert data["status"] == "DRAFT"
    assert "electronics" in data["tags"]
    assert "id" in data


@pytest.mark.asyncio
async def test_create_product_duplicate_slug(client: AsyncClient, auth_headers: dict):
    """Test that creating product with duplicate slug fails."""
    # Create first product
    await client.post(
        "/admin/products",
        json={
            "name": "Product One",
            "slug": "duplicate-slug",
            "description_short": "First product",
        },
        headers=auth_headers,
    )

    # Try to create second product with same slug
    response = await client.post(
        "/admin/products",
        json={
            "name": "Product Two",
            "slug": "duplicate-slug",
            "description_short": "Second product",
        },
        headers=auth_headers,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_product_success(client: AsyncClient, auth_headers: dict):
    """Test updating a product successfully."""
    # Create product
    create_response = await client.post(
        "/admin/products",
        json={
            "name": "Original Name",
            "slug": "original-name",
            "description_short": "Original",
        },
        headers=auth_headers,
    )
    product_id = create_response.json()["id"]

    # Update product
    response = await client.patch(
        f"/admin/products/{product_id}",
        json={
            "name": "Updated Name",
            "description_short": "Updated description",
            "featured": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description_short"] == "Updated description"
    assert data["featured"] is True


@pytest.mark.asyncio
async def test_add_variant_success(client: AsyncClient, auth_headers: dict):
    """Test adding a variant to a product."""
    # Create product
    create_response = await client.post(
        "/admin/products",
        json={"name": "Product with Variant", "slug": "product-variant"},
        headers=auth_headers,
    )
    product_id = create_response.json()["id"]

    # Add variant with dimensions
    response = await client.post(
        f"/admin/products/{product_id}/variants",
        json={
            "sku": "TEST-SKU-001",
            "barcode": "1234567890",
            "price_amount": 1999,
            "price_currency": "USD",
            "compare_at_price_amount": 2499,
            "compare_at_price_currency": "USD",
            "weight": 500,
            "length": 100,
            "width": 50,
            "height": 25,
            "is_default": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "TEST-SKU-001"
    assert data["status"] == "ACTIVE"
    assert data["price"]["amount"] == 1999
    assert data["price"]["currency"] == "USD"
    assert data["weight"] == 500
    assert data["length"] == 100
    assert data["width"] == 50
    assert data["height"] == 25
    assert data["is_default"] is True


@pytest.mark.asyncio
async def test_publish_product_workflow(client: AsyncClient, auth_headers: dict):
    """Test full product publish workflow."""
    # Create product
    create_response = await client.post(
        "/admin/products",
        json={"name": "Publishable Product", "slug": "publishable-product"},
        headers=auth_headers,
    )
    product_id = create_response.json()["id"]

    # Try to publish without variant (should fail)
    publish_response = await client.post(
        f"/admin/products/{product_id}/publish", headers=auth_headers
    )
    assert publish_response.status_code == 400

    # Add variant
    await client.post(
        f"/admin/products/{product_id}/variants",
        json={
            "sku": "PUB-SKU-001",
            "price_amount": 1000,
            "price_currency": "USD",
            "is_default": True,
        },
        headers=auth_headers,
    )

    # Publish should now succeed
    publish_response = await client.post(
        f"/admin/products/{product_id}/publish", headers=auth_headers
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "PUBLISHED"


@pytest.mark.asyncio
async def test_archive_product_success(client: AsyncClient, auth_headers: dict):
    """Test archiving a product."""
    # Create and publish product
    create_response = await client.post(
        "/admin/products",
        json={"name": "Product to Archive", "slug": "archive-product"},
        headers=auth_headers,
    )
    product_id = create_response.json()["id"]

    # Add variant and publish
    await client.post(
        f"/admin/products/{product_id}/variants",
        json={
            "sku": "ARCH-SKU-001",
            "price_amount": 1000,
            "price_currency": "USD",
            "is_default": True,
        },
        headers=auth_headers,
    )
    await client.post(f"/admin/products/{product_id}/publish", headers=auth_headers)

    # Archive
    response = await client.post(
        f"/admin/products/{product_id}/archive", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ARCHIVED"


@pytest.mark.asyncio
async def test_adjust_stock_success(client: AsyncClient, auth_headers: dict):
    """Test adjusting stock for a variant."""
    # Create product and variant
    create_response = await client.post(
        "/admin/products",
        json={"name": "Stock Test Product", "slug": "stock-test"},
        headers=auth_headers,
    )
    product_id = create_response.json()["id"]

    variant_response = await client.post(
        f"/admin/products/{product_id}/variants",
        json={
            "sku": "STOCK-SKU-001",
            "price_amount": 1000,
            "price_currency": "USD",
            "is_default": True,
        },
        headers=auth_headers,
    )
    variant_id = variant_response.json()["id"]

    # Adjust stock
    response = await client.post(
        f"/admin/products/variants/{variant_id}/stock-adjustments",
        json={"delta": 50, "reason": "initial_stock", "note": "Initial inventory"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["on_hand"] == 50
    assert data["available"] == 50


@pytest.mark.asyncio
async def test_add_product_image_success(client: AsyncClient, auth_headers: dict):
    """Test adding an image to a product."""
    # Create product
    create_response = await client.post(
        "/admin/products",
        json={"name": "Product with Image", "slug": "product-image"},
        headers=auth_headers,
    )
    product_id = create_response.json()["id"]

    # Add image
    response = await client.post(
        f"/admin/products/{product_id}/images",
        json={"url": "https://example.com/image.jpg", "alt_text": "Product image"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["url"] == "https://example.com/image.jpg"
    assert data["alt_text"] == "Product image"
    assert data["position"] == 0


@pytest.mark.asyncio
async def test_reorder_images(client: AsyncClient, auth_headers: dict):
    """Test reordering product images."""
    # Create product
    create_response = await client.post(
        "/admin/products",
        json={"name": "Product Multi Image", "slug": "product-multi-image"},
        headers=auth_headers,
    )
    product_id = create_response.json()["id"]

    # Add three images
    image1 = await client.post(
        f"/admin/products/{product_id}/images",
        json={"url": "https://example.com/image1.jpg", "alt_text": "Image 1"},
        headers=auth_headers,
    )
    image2 = await client.post(
        f"/admin/products/{product_id}/images",
        json={"url": "https://example.com/image2.jpg", "alt_text": "Image 2"},
        headers=auth_headers,
    )
    image3 = await client.post(
        f"/admin/products/{product_id}/images",
        json={"url": "https://example.com/image3.jpg", "alt_text": "Image 3"},
        headers=auth_headers,
    )

    image1_id = image1.json()["id"]
    image2_id = image2.json()["id"]
    image3_id = image3.json()["id"]

    # Reorder (swap positions)
    response = await client.post(
        f"/admin/products/{product_id}/images/reorder",
        json={"image_positions": {image1_id: 2, image2_id: 0, image3_id: 1}},
        headers=auth_headers,
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_products_admin_pagination(client: AsyncClient, auth_headers: dict):
    """Test admin product list with pagination."""
    # Create multiple products
    for i in range(5):
        await client.post(
            "/admin/products",
            json={"name": f"Product {i}", "slug": f"product-{i}"},
            headers=auth_headers,
        )

    # Get first page
    response = await client.get(
        "/admin/products?page=1&page_size=3", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 5
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_list_products_filter_by_status(client: AsyncClient, auth_headers: dict):
    """Test filtering products by status."""
    # Create draft product
    draft_response = await client.post(
        "/admin/products",
        json={"name": "Draft Product", "slug": "draft-product"},
        headers=auth_headers,
    )
    draft_id = draft_response.json()["id"]

    # Create and publish another product
    published_response = await client.post(
        "/admin/products",
        json={"name": "Published Product", "slug": "published-product"},
        headers=auth_headers,
    )
    published_id = published_response.json()["id"]

    # Add variant and publish
    await client.post(
        f"/admin/products/{published_id}/variants",
        json={
            "sku": "PUB-FILTER-001",
            "price_amount": 1000,
            "price_currency": "USD",
            "is_default": True,
        },
        headers=auth_headers,
    )
    await client.post(f"/admin/products/{published_id}/publish", headers=auth_headers)

    # Filter by DRAFT
    draft_filter_response = await client.get(
        "/admin/products?status=DRAFT", headers=auth_headers
    )
    draft_products = draft_filter_response.json()["items"]
    assert all(p["status"] == "DRAFT" for p in draft_products)

    # Filter by PUBLISHED
    published_filter_response = await client.get(
        "/admin/products?status=PUBLISHED", headers=auth_headers
    )
    published_products = published_filter_response.json()["items"]
    assert all(p["status"] == "PUBLISHED" for p in published_products)


@pytest.mark.asyncio
async def test_storefront_list_only_published(client: AsyncClient, auth_headers: dict):
    """Test that storefront only shows published products."""
    # Create draft product
    await client.post(
        "/admin/products",
        json={"name": "Draft Storefront", "slug": "draft-storefront"},
        headers=auth_headers,
    )

    # Create and publish product
    published_response = await client.post(
        "/admin/products",
        json={"name": "Published Storefront", "slug": "published-storefront"},
        headers=auth_headers,
    )
    published_id = published_response.json()["id"]

    await client.post(
        f"/admin/products/{published_id}/variants",
        json={
            "sku": "STORE-PUB-001",
            "price_amount": 1000,
            "price_currency": "USD",
            "is_default": True,
        },
        headers=auth_headers,
    )
    await client.post(f"/admin/products/{published_id}/publish", headers=auth_headers)

    # Query storefront (no auth required)
    response = await client.get("/store/products")

    assert response.status_code == 200
    products = response.json()["items"]
    # Should only see published product
    assert all(p["status"] == "PUBLISHED" for p in products)
    assert any(p["slug"] == "published-storefront" for p in products)
    assert not any(p["slug"] == "draft-storefront" for p in products)


@pytest.mark.asyncio
async def test_storefront_get_by_slug(client: AsyncClient, auth_headers: dict):
    """Test getting published product by slug on storefront."""
    # Create and publish product
    create_response = await client.post(
        "/admin/products",
        json={"name": "Slug Test Product", "slug": "slug-test-product"},
        headers=auth_headers,
    )
    product_id = create_response.json()["id"]

    await client.post(
        f"/admin/products/{product_id}/variants",
        json={
            "sku": "SLUG-TEST-001",
            "price_amount": 2999,
            "price_currency": "USD",
            "is_default": True,
        },
        headers=auth_headers,
    )
    await client.post(f"/admin/products/{product_id}/publish", headers=auth_headers)

    # Get by slug on storefront (no auth)
    response = await client.get("/store/products/slug-test-product")

    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "slug-test-product"
    assert data["name"] == "Slug Test Product"
    assert len(data["variants"]) == 1
    assert data["variants"][0]["sku"] == "SLUG-TEST-001"


@pytest.mark.asyncio
async def test_storefront_does_not_show_cost(client: AsyncClient, auth_headers: dict):
    """Test that storefront hides cost field."""
    # Create product with variant including cost
    create_response = await client.post(
        "/admin/products",
        json={"name": "Cost Hidden Product", "slug": "cost-hidden"},
        headers=auth_headers,
    )
    product_id = create_response.json()["id"]

    await client.post(
        f"/admin/products/{product_id}/variants",
        json={
            "sku": "COST-TEST-001",
            "price_amount": 2999,
            "price_currency": "USD",
            "cost_amount": 1500,
            "cost_currency": "USD",
            "is_default": True,
        },
        headers=auth_headers,
    )
    await client.post(f"/admin/products/{product_id}/publish", headers=auth_headers)

    # Get from storefront
    response = await client.get("/store/products/cost-hidden")

    assert response.status_code == 200
    data = response.json()
    # Cost should not be in variant response
    assert "cost" not in data["variants"][0]


@pytest.mark.asyncio
async def test_create_category_success(client: AsyncClient, auth_headers: dict):
    """Test creating a category."""
    response = await client.post(
        "/admin/categories",
        json={"name": "Electronics", "slug": "electronics", "description": "Electronic items"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Electronics"
    assert data["slug"] == "electronics"


@pytest.mark.asyncio
async def test_assign_categories_to_product(client: AsyncClient, auth_headers: dict):
    """Test assigning categories to a product."""
    # Create categories
    cat1_response = await client.post(
        "/admin/categories",
        json={"name": "Category 1", "slug": "category-1"},
        headers=auth_headers,
    )
    cat2_response = await client.post(
        "/admin/categories",
        json={"name": "Category 2", "slug": "category-2"},
        headers=auth_headers,
    )

    cat1_id = cat1_response.json()["id"]
    cat2_id = cat2_response.json()["id"]

    # Create product
    product_response = await client.post(
        "/admin/products",
        json={"name": "Categorized Product", "slug": "categorized-product"},
        headers=auth_headers,
    )
    product_id = product_response.json()["id"]

    # Assign categories
    response = await client.post(
        f"/admin/products/{product_id}/categories",
        json={"category_ids": [cat1_id, cat2_id]},
        headers=auth_headers,
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_product_with_variants_and_dimensions(client: AsyncClient, auth_headers: dict):
    """Test GET /admin/products/{product_id} returns variants with dimensions correctly."""
    # Create product
    create_response = await client.post(
        "/admin/products",
        json={"name": "Product with Variants", "slug": "product-with-variants"},
        headers=auth_headers,
    )
    product_id = create_response.json()["id"]

    # Add variant with full dimensions
    variant_response = await client.post(
        f"/admin/products/{product_id}/variants",
        json={
            "sku": "VARIANT-001",
            "barcode": "9876543210",
            "price_amount": 2999,
            "price_currency": "USD",
            "weight": 750,
            "length": 150,
            "width": 100,
            "height": 50,
            "is_default": True,
        },
        headers=auth_headers,
    )
    assert variant_response.status_code == 201

    # Add second variant with partial dimensions
    variant2_response = await client.post(
        f"/admin/products/{product_id}/variants",
        json={
            "sku": "VARIANT-002",
            "price_amount": 1999,
            "price_currency": "USD",
            "weight": 500,
            "is_default": False,
        },
        headers=auth_headers,
    )
    assert variant2_response.status_code == 201

    # Get product detail
    response = await client.get(f"/admin/products/{product_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Verify product details
    assert data["product"]["id"] == product_id
    assert data["product"]["name"] == "Product with Variants"
    assert data["product"]["slug"] == "product-with-variants"

    # Verify variants are returned
    assert "variants" in data
    assert len(data["variants"]) == 2

    # Find and verify first variant (full dimensions)
    variant1 = next(v for v in data["variants"] if v["sku"] == "VARIANT-001")
    assert variant1["weight"] == 750
    assert variant1["length"] == 150
    assert variant1["width"] == 100
    assert variant1["height"] == 50
    assert variant1["barcode"] == "9876543210"
    assert variant1["is_default"] is True

    # Find and verify second variant (partial dimensions)
    variant2 = next(v for v in data["variants"] if v["sku"] == "VARIANT-002")
    assert variant2["weight"] == 500
    assert variant2["length"] is None
    assert variant2["width"] is None
    assert variant2["height"] is None
    assert variant2["is_default"] is False


