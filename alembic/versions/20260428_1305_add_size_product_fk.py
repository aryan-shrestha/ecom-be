"""add size product foreign key

Revision ID: b0f3d1c7c1a2
Revises: 8a2829eaead7
Create Date: 2026-04-28 13:05:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "b0f3d1c7c1a2"
down_revision = "8a2829eaead7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_sizes_product_id_products",
        "sizes",
        "products",
        ["product_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_sizes_product_id_products", "sizes", type_="foreignkey")
