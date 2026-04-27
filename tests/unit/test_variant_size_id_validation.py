"""Unit tests for ProductVariant size_id validation."""

import uuid
from datetime import datetime

from app.domain.entities.product_variant import ProductVariant, VariantStatus
from app.domain.value_objects.money import Money
from app.domain.value_objects.sku import SKU


def test_variant_size_id_uuid_does_not_raise():
    """size_id is a UUID and should not be treated like a string length."""
    variant = ProductVariant(
        id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        sku=SKU.from_string("SKU-TEST-001"),
        barcode=None,
        status=VariantStatus.ACTIVE,
        price=Money(amount=1000, currency="USD"),
        compare_at_price=None,
        cost=None,
        color_id=None,
        size_id=uuid.uuid4(),
        is_default=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert variant.size_id is not None
