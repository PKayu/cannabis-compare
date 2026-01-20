"""Initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-01-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Dispensaries
    op.create_table('dispensaries',
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
    op.create_index(op.f('ix_dispensaries_name'), 'dispensaries', ['name'], unique=False)

    # Brands
    op.create_table('brands',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_brands_name'), 'brands', ['name'], unique=True)

    # Products
    op.create_table('products',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('product_type', sa.String(), nullable=False),
        sa.Column('thc_percentage', sa.Float(), nullable=True),
        sa.Column('cbd_percentage', sa.Float(), nullable=True),
        sa.Column('brand_id', sa.String(), nullable=False),
        sa.Column('master_product_id', sa.String(), nullable=True),
        sa.Column('normalization_confidence', sa.Float(), nullable=True),
        sa.Column('is_master', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ),
        sa.ForeignKeyConstraint(['master_product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)

    # Prices
    op.create_table('prices',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('in_stock', sa.Boolean(), nullable=True),
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

    # Reviews
    op.create_table('reviews',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('effects_rating', sa.Integer(), nullable=True),
        sa.Column('taste_rating', sa.Integer(), nullable=True),
        sa.Column('value_rating', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('upvotes', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Scraper Flags
    op.create_table('scraper_flags',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('original_name', sa.String(), nullable=False),
        sa.Column('original_thc', sa.Float(), nullable=True),
        sa.Column('original_cbd', sa.Float(), nullable=True),
        sa.Column('brand_name', sa.String(), nullable=False),
        sa.Column('dispensary_id', sa.String(), nullable=False),
        sa.Column('matched_product_id', sa.String(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
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
    op.create_index(op.f('ix_scraper_flags_status'), 'scraper_flags', ['status'], unique=False)

    # Promotions
    op.create_table('promotions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('discount_percentage', sa.Float(), nullable=True),
        sa.Column('discount_amount', sa.Float(), nullable=True),
        sa.Column('dispensary_id', sa.String(), nullable=False),
        sa.Column('product_id', sa.String(), nullable=True),
        sa.Column('applies_to_category', sa.String(), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=True),
        sa.Column('recurring_pattern', sa.String(), nullable=True),
        sa.Column('recurring_day', sa.String(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dispensary_id'], ['dispensaries.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_promotions_dispensary_id'), 'promotions', ['dispensary_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_promotions_dispensary_id'), table_name='promotions')
    op.drop_table('promotions')
    op.drop_index(op.f('ix_scraper_flags_status'), table_name='scraper_flags')
    op.drop_table('scraper_flags')
    op.drop_table('reviews')
    op.drop_table('prices')
    op.drop_index(op.f('ix_products_name'), table_name='products')
    op.drop_table('products')
    op.drop_index(op.f('ix_brands_name'), table_name='brands')
    op.drop_table('brands')
    op.drop_index(op.f('ix_dispensaries_name'), table_name='dispensaries')
    op.drop_table('dispensaries')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')