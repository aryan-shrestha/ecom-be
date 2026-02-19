"""Unit tests for ProductPublishPolicy."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from app.domain.entities.product import Product, ProductStatus
from app.domain.entities.product_variant import ProductVariant, VariantStatus
from app.domain.value_objects.slug import Slug
from app.domain.value_objects.sku import SKU
from app.domain.value_objects.money import Money
from app.domain.policies.product_publish_policy import ProductPublishPolicy


class TestProductPublishPolicy:
    """Test cases for ProductPublishPolicy."""

    def test_can_publish_valid_product(self):
        """Test that a valid product can be published."""
        product_id = uuid4()
        product = Product(
            id=product_id,
            name="Test Product",
            slug=Slug("test-product"),
            description_short="Test",
            description_long=None,
            status=ProductStatus.DRAFT,
            tags=[],
            featured=False,
            sort_order=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=uuid4(),
            updated_by=uuid4(),
        )

        variant = ProductVariant(
            id=uuid4(),
            product_id=product_id,
            sku=SKU("TEST-SKU"),
            barcode=None,
            status=VariantStatus.ACTIVE,
            price=Money(amount_minor=1000, currency="USD"),
            compare_at_price=None,
            cost=None,
            weight_grams=None,
            length_mm=None,
            width_mm=None,
            height_mm=None,
            is_default=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        can_publish, reason = ProductPublishPolicy.can_publish(product, [variant])

        assert can_publish is True
        assert reason is None

    def test_cannot_publish_without_name(self):
        """Test that product without name cannot be published."""
        product = Product(
            id=uuid4(),
            name="",
            slug=Slug("test-product"),
            description_short=None,
            description_long=None,
            status=ProductStatus.DRAFT,
            tags=[],
            featured=False,
            sort_order=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=uuid4(),
            updated_by=uuid4(),
        )

        can_publish, reason = ProductPublishPolicy.can_publish(product, [])

        assert can_publish is False
        assert "name" in reason.lower()

    def test_cannot_publish_without_slug(self):
        """Test that product without slug cannot be published."""
        product = Product(
            id=uuid4(),
            name="Test Product",
            slug=None,
            description_short=None,
            description_long=None,
            status=ProductStatus.DRAFT,
            tags=[],
            featured=False,
            sort_order=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=uuid4(),
            updated_by=uuid4(),
        )

        can_publish, reason = ProductPublishPolicy.can_publish(product, [])

        assert can_publish is False
        assert "slug" in reason.lower()

    def test_cannot_publish_without_active_variants(self):
        """Test that product without active variants cannot be published."""
        product = Product(
            id=uuid4(),
            name="Test Product",
            slug=Slug("test-product"),
            description_short=None,
            description_long=None,
            status=ProductStatus.DRAFT,
            tags=[],
            featured=False,
            sort_order=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=uuid4(),
            updated_by=uuid4(),
        )

        can_publish, reason = ProductPublishPolicy.can_publish(product, [])

        assert can_publish is False
        assert "variant" in reason.lower()

    def test_cannot_publish_with_only_inactive_variants(self):
        """Test that product with only inactive variants cannot be published."""
        product_id = uuid4()
        product = Product(
            id=product_id,
            name="Test Product",
            slug=Slug("test-product"),
            description_short=None,
            description_long=None,
            status=ProductStatus.DRAFT,
            tags=[],
            featured=False,
            sort_order=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=uuid4(),
            updated_by=uuid4(),
        )

        inactive_variant = ProductVariant(
            id=uuid4(),
            product_id=product_id,
            sku=SKU("TEST-SKU"),
            barcode=None,
            status=VariantStatus.INACTIVE,
            price=Money(amount_minor=1000, currency="USD"),
            compare_at_price=None,
            cost=None,
            weight_grams=None,
            length_mm=None,
            width_mm=None,
            height_mm=None,
            is_default=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        can_publish, reason = ProductPublishPolicy.can_publish(product, [inactive_variant])

        assert can_publish is False
        assert "active" in reason.lower()

    def test_cannot_publish_with_variant_missing_sku(self):
        """Test that product with variant missing SKU cannot be published."""
        product_id = uuid4()
        product = Product(
            id=product_id,
            name="Test Product",
            slug=Slug("test-product"),
            description_short=None,
            description_long=None,
            status=ProductStatus.DRAFT,
            tags=[],
            featured=False,
            sort_order=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=uuid4(),
            updated_by=uuid4(),
        )

        variant = ProductVariant(
            id=uuid4(),
            product_id=product_id,
            sku=None,
            barcode=None,
            status=VariantStatus.ACTIVE,
            price=Money(amount_minor=1000, currency="USD"),
            compare_at_price=None,
            cost=None,
            weight_grams=None,
            length_mm=None,
            width_mm=None,
            height_mm=None,
            is_default=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        can_publish, reason = ProductPublishPolicy.can_publish(product, [variant])

        assert can_publish is False
        assert "sku" in reason.lower()

    def test_cannot_publish_with_variant_missing_price(self):
        """Test that product with variant missing price cannot be published."""
        product_id = uuid4()
        product = Product(
            id=product_id,
            name="Test Product",
            slug=Slug("test-product"),
            description_short=None,
            description_long=None,
            status=ProductStatus.DRAFT,
            tags=[],
            featured=False,
            sort_order=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=uuid4(),
            updated_by=uuid4(),
        )

        variant = ProductVariant(
            id=uuid4(),
            product_id=product_id,
            sku=SKU("TEST-SKU"),
            barcode=None,
            status=VariantStatus.ACTIVE,
            price=None,
            compare_at_price=None,
            cost=None,
            weight_grams=None,
            length_mm=None,
            width_mm=None,
            height_mm=None,
            is_default=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        can_publish, reason = ProductPublishPolicy.can_publish(product, [variant])

        assert can_publish is False
        assert "price" in reason.lower()

    def test_can_publish_with_multiple_variants_some_active(self):
        """Test that product can be published if at least one variant is valid and active."""
        product_id = uuid4()
        product = Product(
            id=product_id,
            name="Test Product",
            slug=Slug("test-product"),
            description_short=None,
            description_long=None,
            status=ProductStatus.DRAFT,
            tags=[],
            featured=False,
            sort_order=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=uuid4(),
            updated_by=uuid4(),
        )

        active_variant = ProductVariant(
            id=uuid4(),
            product_id=product_id,
            sku=SKU("TEST-SKU-1"),
            barcode=None,
            status=VariantStatus.ACTIVE,
            price=Money(amount_minor=1000, currency="USD"),
            compare_at_price=None,
            cost=None,
            weight_grams=None,
            length_mm=None,
            width_mm=None,
            height_mm=None,
            is_default=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        inactive_variant = ProductVariant(
            id=uuid4(),
            product_id=product_id,
            sku=SKU("TEST-SKU-2"),
            barcode=None,
            status=VariantStatus.INACTIVE,
            price=Money(amount_minor=1500, currency="USD"),
            compare_at_price=None,
            cost=None,
            weight_grams=None,
            length_mm=None,
            width_mm=None,
            height_mm=None,
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        can_publish, reason = ProductPublishPolicy.can_publish(
            product, [active_variant, inactive_variant]
        )

        assert can_publish is True
        assert reason is None

