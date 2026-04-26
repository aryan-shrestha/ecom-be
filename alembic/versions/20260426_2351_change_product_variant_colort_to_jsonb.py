"""change product variant colort to jsonb

Revision ID: c6c38e0900e6
Revises: 69cb41a74d11
Create Date: 2026-04-26 23:51:36.220958

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c6c38e0900e6'
down_revision = '69cb41a74d11'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "product_variants",
        "color",
        existing_type=sa.String(),
        type_=postgresql.JSONB(),
        existing_nullable=True,
        postgresql_using="""
        CASE
            WHEN color IS NULL THEN NULL
            WHEN color = '' THEN NULL
            ELSE jsonb_build_object('name', color, 'hex_code', NULL)
        END
        """,
    )


def downgrade():
    op.alter_column(
        "product_variants",
        "color",
        existing_type=postgresql.JSONB(),
        type_=sa.String(),
        existing_nullable=True,
        postgresql_using="color ->> 'name'",
    )