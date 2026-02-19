"""Add product management tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable uuid extension (if not already enabled)
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='RESTRICT'),
    )
    
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False, unique=True, index=True),
        sa.Column('description_short', sa.String(500), nullable=True),
        sa.Column('description_long', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, index=True),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('featured', sa.Boolean(), nullable=False, default=False, index=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    
    # Create GIN index on tags JSONB column for faster JSONB queries
    op.create_index(
        'ix_products_tags',
        'products',
        ['tags'],
        postgresql_using='gin'
    )
    
    # Create composite index for common storefront queries (status + created_at)
    op.create_index(
        'ix_products_status_created_at',
        'products',
        ['status', 'created_at']
    )
    
    # Create product_variants table
    op.create_table(
        'product_variants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('sku', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('barcode', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, index=True),
        sa.Column('price_amount', sa.Integer(), nullable=False),
        sa.Column('price_currency', sa.String(3), nullable=False),
        sa.Column('compare_at_price_amount', sa.Integer(), nullable=True),
        sa.Column('compare_at_price_currency', sa.String(3), nullable=True),
        sa.Column('cost_amount', sa.Integer(), nullable=True),
        sa.Column('cost_currency', sa.String(3), nullable=True),
        sa.Column('weight_grams', sa.Integer(), nullable=True),
        sa.Column('length_mm', sa.Integer(), nullable=True),
        sa.Column('width_mm', sa.Integer(), nullable=True),
        sa.Column('height_mm', sa.Integer(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
    )
    
    # Create product_categories M2M table
    op.create_table(
        'product_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('product_id', 'category_id', name='uq_product_category'),
    )
    
    # Create inventory table
    op.create_table(
        'inventory',
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('on_hand', sa.Integer(), nullable=False, default=0),
        sa.Column('reserved', sa.Integer(), nullable=False, default=0),
        sa.Column('allow_backorder', sa.Boolean(), nullable=False, default=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['variant_id'], ['product_variants.id'], ondelete='CASCADE'),
    )
    
    # Create stock_movements table (audit trail)
    op.create_table(
        'stock_movements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('delta', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(100), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), index=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['variant_id'], ['product_variants.id'], ondelete='CASCADE'),
    )
    
    # Create product_images table
    op.create_table(
        'product_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('url', sa.String(1000), nullable=False),
        sa.Column('alt_text', sa.String(255), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
    )
    
    # Create composite index for product_images ordering
    op.create_index(
        'ix_product_images_product_id_position',
        'product_images',
        ['product_id', 'position']
    )


def downgrade() -> None:
    op.drop_table('product_images')
    op.drop_table('stock_movements')
    op.drop_table('inventory')
    op.drop_table('product_categories')
    op.drop_table('product_variants')
    op.drop_index('ix_products_status_created_at', 'products')
    op.drop_index('ix_products_tags', 'products')
    op.drop_table('products')
    op.drop_table('categories')
    # Note: Not dropping uuid-ossp extension as it may be used by other migrations

