"""Add cart and order management tables

Revision ID: 004
Revises: 003
Create Date: 2026-03-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # carts
    # -------------------------------------------------------------------------
    op.create_table(
        'carts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('status', sa.String(20), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('guest_token', sa.String(128), nullable=True, index=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    # Partial index: at most one ACTIVE cart per user
    op.create_index(
        'ix_carts_active_user',
        'carts',
        ['user_id'],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE' AND user_id IS NOT NULL"),
    )
    # Partial index: at most one ACTIVE cart per guest token
    op.create_index(
        'ix_carts_active_guest',
        'carts',
        ['guest_token'],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE' AND guest_token IS NOT NULL"),
    )

    # -------------------------------------------------------------------------
    # cart_items
    # -------------------------------------------------------------------------
    op.create_table(
        'cart_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('cart_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['cart_id'], ['carts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['product_variants.id'], ondelete='RESTRICT'),
        sa.UniqueConstraint('cart_id', 'variant_id', name='uq_cart_items_cart_variant'),
    )

    # -------------------------------------------------------------------------
    # orders
    # -------------------------------------------------------------------------
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('order_number', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('status', sa.String(30), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('guest_token', sa.String(128), nullable=True, index=True),
        sa.Column('subtotal_amount', sa.Integer(), nullable=False),
        sa.Column('grand_total_amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('shipping_address', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'), index=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # -------------------------------------------------------------------------
    # order_items
    # -------------------------------------------------------------------------
    op.create_table(
        'order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('variant_sku', sa.String(100), nullable=False),
        sa.Column('variant_label', sa.String(255), nullable=True),
        sa.Column('unit_price_amount', sa.Integer(), nullable=False),
        sa.Column('unit_price_currency', sa.String(3), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    )

    # -------------------------------------------------------------------------
    # idempotency_keys
    # -------------------------------------------------------------------------
    op.create_table(
        'idempotency_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('scope', sa.String(50), nullable=False, index=True),
        sa.Column('actor_identifier', sa.String(128), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'), index=True),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False, index=True),
        sa.UniqueConstraint('scope', 'actor_identifier', 'key',
                            name='uq_idempotency_scope_actor_key'),
    )


def downgrade() -> None:
    op.drop_table('idempotency_keys')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('cart_items')
    op.drop_index('ix_carts_active_guest', table_name='carts')
    op.drop_index('ix_carts_active_user', table_name='carts')
    op.drop_table('carts')
