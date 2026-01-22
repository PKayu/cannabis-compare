"""add_search_performance_indexes

Revision ID: 3770f7e5ab14
Revises: 20260119_000001
Create Date: 2026-01-21 19:31:40.513219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3770f7e5ab14'
down_revision: Union[str, None] = '20260119_000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes for search performance optimization"""

    # Index for product name text search (case-insensitive LIKE queries)
    op.create_index(
        'ix_products_name_lower',
        'products',
        [sa.text('LOWER(name)')],
        postgresql_using='btree'
    )

    # Index for product type filtering
    op.create_index(
        'ix_products_product_type',
        'products',
        ['product_type']
    )

    # Index for THC percentage range queries
    op.create_index(
        'ix_products_thc_percentage',
        'products',
        ['thc_percentage']
    )

    # Index for CBD percentage range queries
    op.create_index(
        'ix_products_cbd_percentage',
        'products',
        ['cbd_percentage']
    )

    # Index for product_id in prices table (already exists via FK, but explicit for clarity)
    # Skipping as it's created by foreign key constraint

    # Index for price amount for sorting
    op.create_index(
        'ix_prices_amount',
        'prices',
        ['amount']
    )

    # Index for in_stock filtering
    op.create_index(
        'ix_prices_in_stock',
        'prices',
        ['in_stock']
    )

    # Composite index for product + in_stock queries
    op.create_index(
        'ix_prices_product_id_in_stock',
        'prices',
        ['product_id', 'in_stock']
    )

    # Index for promotion lookups by dispensary
    op.create_index(
        'ix_promotions_dispensary_active',
        'promotions',
        ['dispensary_id', 'is_active']
    )

    # Index for promotion date filtering
    op.create_index(
        'ix_promotions_dates',
        'promotions',
        ['start_date', 'end_date']
    )


def downgrade() -> None:
    """Remove search performance indexes"""

    op.drop_index('ix_promotions_dates', table_name='promotions')
    op.drop_index('ix_promotions_dispensary_active', table_name='promotions')
    op.drop_index('ix_prices_product_id_in_stock', table_name='prices')
    op.drop_index('ix_prices_in_stock', table_name='prices')
    op.drop_index('ix_prices_amount', table_name='prices')
    op.drop_index('ix_products_cbd_percentage', table_name='products')
    op.drop_index('ix_products_thc_percentage', table_name='products')
    op.drop_index('ix_products_product_type', table_name='products')
    op.drop_index('ix_products_name_lower', table_name='products')
