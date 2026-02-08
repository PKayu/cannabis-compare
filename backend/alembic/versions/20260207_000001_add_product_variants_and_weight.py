"""Add product weight columns and scraper flag fields for variant support

Revision ID: a1b2c3d4e5f6
Revises: d61ee6846ddf
Create Date: 2026-02-07 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'd61ee6846ddf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Product table: add weight columns for variant products
    op.add_column('products', sa.Column('weight', sa.String(), nullable=True))
    op.add_column('products', sa.Column('weight_grams', sa.Float(), nullable=True))

    # Product table: add indexes for variant queries
    op.create_index('ix_products_weight_grams', 'products', ['weight_grams'])
    op.create_index('ix_products_is_master', 'products', ['is_master'])
    op.create_index('ix_products_master_product_id', 'products', ['master_product_id'])

    # ScraperFlag table: add original scraped data fields for variant creation on resolution
    op.add_column('scraper_flags', sa.Column('original_weight', sa.String(), nullable=True))
    op.add_column('scraper_flags', sa.Column('original_price', sa.Float(), nullable=True))
    op.add_column('scraper_flags', sa.Column('original_category', sa.String(), nullable=True))


def downgrade() -> None:
    # ScraperFlag: remove added columns
    op.drop_column('scraper_flags', 'original_category')
    op.drop_column('scraper_flags', 'original_price')
    op.drop_column('scraper_flags', 'original_weight')

    # Product: remove indexes and columns
    op.drop_index('ix_products_master_product_id', table_name='products')
    op.drop_index('ix_products_is_master', table_name='products')
    op.drop_index('ix_products_weight_grams', table_name='products')
    op.drop_column('products', 'weight_grams')
    op.drop_column('products', 'weight')
