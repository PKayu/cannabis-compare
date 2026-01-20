"""Initial schema with all tables and indexes

Revision ID: 20260119_000001
Revises:
Create Date: 2026-01-19

Creates the following tables:
- users: User accounts for authentication
- brands: Cannabis cultivators/brands
- dispensaries: Utah pharmacy details
- products: Master product entries
- prices: Junction table linking products to dispensaries
- reviews: User reviews with intention tags
- scraper_flags: Products requiring manual normalization review
- promotions: Recurring and one-time promotional offers
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260119_000001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === Users table ===
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # === Brands table ===
    op.create_table(
        'brands',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_brands_name', 'brands', ['name'])

    # === Dispensaries table ===
    op.create_table(
        'dispensaries',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('hours', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dispensaries_name', 'dispensaries', ['name'])

    # === Products table ===
    op.create_table(
        'products',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('product_type', sa.String(), nullable=False),
        sa.Column('thc_percentage', sa.Float(), nullable=True),
        sa.Column('cbd_percentage', sa.Float(), nullable=True),
        sa.Column('brand_id', sa.String(), nullable=False),
        sa.Column('master_product_id', sa.String(), nullable=True),
        sa.Column('normalization_confidence', sa.Float(), nullable=True, default=1.0),
        sa.Column('is_master', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ),
        sa.ForeignKeyConstraint(['master_product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_products_name', 'products', ['name'])
    op.create_index('ix_products_brand_id', 'products', ['brand_id'])
    op.create_index('ix_products_product_type', 'products', ['product_type'])

    # === Prices table ===
    op.create_table(
        'prices',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('in_stock', sa.Boolean(), nullable=True, default=True),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('dispensary_id', sa.String(), nullable=False),
        sa.Column('previous_price', sa.Float(), nullable=True),
        sa.Column('price_change_date', sa.DateTime(), nullable=True),
        sa.Column('price_change_percentage', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dispensary_id'], ['dispensaries.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'dispensary_id', name='uix_product_dispensary')
    )
    op.create_index('ix_prices_product_id', 'prices', ['product_id'])
    op.create_index('ix_prices_dispensary_id', 'prices', ['dispensary_id'])

    # === Reviews table ===
    op.create_table(
        'reviews',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('effects_rating', sa.Integer(), nullable=True),
        sa.Column('taste_rating', sa.Integer(), nullable=True),
        sa.Column('value_rating', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('upvotes', sa.Integer(), nullable=True, default=0),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reviews_product_id', 'reviews', ['product_id'])
    op.create_index('ix_reviews_user_id', 'reviews', ['user_id'])

    # === ScraperFlags table ===
    op.create_table(
        'scraper_flags',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('original_name', sa.String(), nullable=False),
        sa.Column('original_thc', sa.Float(), nullable=True),
        sa.Column('original_cbd', sa.Float(), nullable=True),
        sa.Column('brand_name', sa.String(), nullable=False),
        sa.Column('dispensary_id', sa.String(), nullable=False),
        sa.Column('matched_product_id', sa.String(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), nullable=True, default='pending'),
        sa.Column('merge_reason', sa.String(), nullable=True),
        sa.Column('admin_notes', sa.String(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dispensary_id'], ['dispensaries.id'], ),
        sa.ForeignKeyConstraint(['matched_product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scraper_flags_status', 'scraper_flags', ['status'])
    op.create_index('ix_scraper_flags_dispensary_id', 'scraper_flags', ['dispensary_id'])

    # === Promotions table ===
    op.create_table(
        'promotions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('discount_percentage', sa.Float(), nullable=True),
        sa.Column('discount_amount', sa.Float(), nullable=True),
        sa.Column('dispensary_id', sa.String(), nullable=False),
        sa.Column('product_id', sa.String(), nullable=True),
        sa.Column('applies_to_category', sa.String(), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=True, default=False),
        sa.Column('recurring_pattern', sa.String(), nullable=True),
        sa.Column('recurring_day', sa.String(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dispensary_id'], ['dispensaries.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_promotions_dispensary_id', 'promotions', ['dispensary_id'])
    op.create_index('ix_promotions_is_active', 'promotions', ['is_active'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_index('ix_promotions_is_active', 'promotions')
    op.drop_index('ix_promotions_dispensary_id', 'promotions')
    op.drop_table('promotions')

    op.drop_index('ix_scraper_flags_dispensary_id', 'scraper_flags')
    op.drop_index('ix_scraper_flags_status', 'scraper_flags')
    op.drop_table('scraper_flags')

    op.drop_index('ix_reviews_user_id', 'reviews')
    op.drop_index('ix_reviews_product_id', 'reviews')
    op.drop_table('reviews')

    op.drop_index('ix_prices_dispensary_id', 'prices')
    op.drop_index('ix_prices_product_id', 'prices')
    op.drop_table('prices')

    op.drop_index('ix_products_product_type', 'products')
    op.drop_index('ix_products_brand_id', 'products')
    op.drop_index('ix_products_name', 'products')
    op.drop_table('products')

    op.drop_index('ix_dispensaries_name', 'dispensaries')
    op.drop_table('dispensaries')

    op.drop_index('ix_brands_name', 'brands')
    op.drop_table('brands')

    op.drop_index('ix_users_username', 'users')
    op.drop_index('ix_users_email', 'users')
    op.drop_table('users')
