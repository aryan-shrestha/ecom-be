"""Add image storage metadata and variant images

Revision ID: 003
Revises: 002
Create Date: 2026-02-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add storage metadata columns to product_images
    op.add_column('product_images', sa.Column('provider', sa.String(50), nullable=True))
    op.add_column('product_images', sa.Column('provider_public_id', sa.String(500), nullable=True))
    op.add_column('product_images', sa.Column('bytes_size', sa.Integer(), nullable=True))
    op.add_column('product_images', sa.Column('width', sa.Integer(), nullable=True))
    op.add_column('product_images', sa.Column('height', sa.Integer(), nullable=True))
    op.add_column('product_images', sa.Column('format', sa.String(20), nullable=True))
    
    # Create index on provider_public_id for efficient lookups/deletions
    op.create_index(
        'ix_product_images_provider_public_id',
        'product_images',
        ['provider_public_id'],
        unique=False
    )
    
    # Create variant_images table
    op.create_table(
        'variant_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('url', sa.String(1000), nullable=False),
        sa.Column('alt_text', sa.String(255), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('provider_public_id', sa.String(500), nullable=True),
        sa.Column('bytes_size', sa.Integer(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('format', sa.String(20), nullable=True),
        sa.ForeignKeyConstraint(['variant_id'], ['product_variants.id'], ondelete='CASCADE'),
    )
    
    # Create index on variant_id and position for ordering
    op.create_index(
        'ix_variant_images_variant_id_position',
        'variant_images',
        ['variant_id', 'position'],
        unique=False
    )
    
    # Create index on provider_public_id for efficient lookups/deletions
    op.create_index(
        'ix_variant_images_provider_public_id',
        'variant_images',
        ['provider_public_id'],
        unique=False
    )


def downgrade() -> None:
    # Drop variant_images table
    op.drop_table('variant_images')
    
    # Drop added columns from product_images
    op.drop_index('ix_product_images_provider_public_id', table_name='product_images')
    op.drop_column('product_images', 'format')
    op.drop_column('product_images', 'height')
    op.drop_column('product_images', 'width')
    op.drop_column('product_images', 'bytes_size')
    op.drop_column('product_images', 'provider_public_id')
    op.drop_column('product_images', 'provider')
