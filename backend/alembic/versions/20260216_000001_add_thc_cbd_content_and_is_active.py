"""add thc_content, cbd_content, is_active and auto_merged status

Adds plain-text cannabinoid display fields, soft-delete flag, and
auto_merged status support to products and scraper_flags tables.

Revision ID: b2c3d4e5f6a7
Revises: fbc31715966a
Create Date: 2026-02-16 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'fbc31715966a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Products: add plain-text cannabinoid display fields and soft-delete flag
    op.add_column('products', sa.Column('thc_content', sa.String(), nullable=True))
    op.add_column('products', sa.Column('cbd_content', sa.String(), nullable=True))
    op.add_column('products', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'))
    op.create_index(op.f('ix_products_is_active'), 'products', ['is_active'], unique=False)

    # ScraperFlags: add plain-text cannabinoid display fields
    op.add_column('scraper_flags', sa.Column('original_thc_content', sa.String(), nullable=True))
    op.add_column('scraper_flags', sa.Column('original_cbd_content', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('scraper_flags', 'original_cbd_content')
    op.drop_column('scraper_flags', 'original_thc_content')

    op.drop_index(op.f('ix_products_is_active'), table_name='products')
    op.drop_column('products', 'is_active')
    op.drop_column('products', 'cbd_content')
    op.drop_column('products', 'thc_content')
