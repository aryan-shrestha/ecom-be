"""Unit tests for Alembic metadata registration."""

from app.infrastructure.db.sqlalchemy.base import Base
import app.infrastructure.db.sqlalchemy.models  # noqa: F401


def test_metadata_includes_core_tables():
    """All core tables should be registered in Base.metadata."""
    table_names = set(Base.metadata.tables.keys())
    assert "products" in table_names
    assert "product_variants" in table_names
    assert "colors" in table_names
    assert "sizes" in table_names
    assert "users" in table_names
