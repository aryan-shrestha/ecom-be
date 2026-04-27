"""Integration tests for color and size repositories."""

import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.sqlalchemy.models.product_model import ProductModel
from app.infrastructure.db.sqlalchemy.models.color_model import ColorModel
from app.infrastructure.db.sqlalchemy.models.size_model import SizeModel
from app.infrastructure.repositories.sqlalchemy.color_repo import SQLAlchemyColorRepository
from app.infrastructure.repositories.sqlalchemy.size_repo import SQLAlchemySizeRepository


@pytest.mark.asyncio
async def test_color_and_size_list_by_product(session: AsyncSession):
    """List colors/sizes by product ID returns only matching rows."""
    product_id = uuid.uuid4()
    other_product_id = uuid.uuid4()
    now = datetime.utcnow()

    session.add(
        ProductModel(
            id=product_id,
            status="DRAFT",
            name="Repo Product",
            slug="repo-product",
            description_short=None,
            description_long=None,
            tags=[],
            featured=False,
            sort_order=0,
            created_at=now,
            updated_at=now,
        )
    )
    session.add(
        ProductModel(
            id=other_product_id,
            status="DRAFT",
            name="Other Repo Product",
            slug="other-repo-product",
            description_short=None,
            description_long=None,
            tags=[],
            featured=False,
            sort_order=0,
            created_at=now,
            updated_at=now,
        )
    )

    color_a = ColorModel(
        id=uuid.uuid4(),
        name="Black",
        hex_value="#000000",
        product_id=product_id,
        created_at=now,
        updated_at=now,
    )
    color_b = ColorModel(
        id=uuid.uuid4(),
        name="White",
        hex_value="#FFFFFF",
        product_id=other_product_id,
        created_at=now,
        updated_at=now,
    )
    size_a = SizeModel(
        id=uuid.uuid4(),
        name="M",
        product_id=product_id,
        created_at=now,
        updated_at=now,
    )
    size_b = SizeModel(
        id=uuid.uuid4(),
        name="L",
        product_id=other_product_id,
        created_at=now,
        updated_at=now,
    )

    session.add_all([color_a, color_b, size_a, size_b])
    await session.commit()

    color_repo = SQLAlchemyColorRepository(session)
    size_repo = SQLAlchemySizeRepository(session)

    colors = await color_repo.list_by_product_id(product_id)
    sizes = await size_repo.list_by_product_id(product_id)

    assert [c.id for c in colors] == [color_a.id]
    assert [s.id for s in sizes] == [size_a.id]
