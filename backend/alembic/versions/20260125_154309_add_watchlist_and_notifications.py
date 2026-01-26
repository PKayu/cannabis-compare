"""add_watchlist_and_notifications

Revision ID: 5d1e45e38b68
Revises: 3770f7e5ab14
Create Date: 2026-01-25 15:43:09.995743

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d1e45e38b68'
down_revision: Union[str, None] = '3770f7e5ab14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create watchlists table
    op.create_table(
        'watchlists',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('alert_on_stock', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('alert_on_price_drop', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('price_drop_threshold', sa.Float(), nullable=True, server_default='10.0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'product_id', name='uix_user_product')
    )
    op.create_index(op.f('ix_watchlists_product_id'), 'watchlists', ['product_id'], unique=False)
    op.create_index(op.f('ix_watchlists_user_id'), 'watchlists', ['user_id'], unique=False)

    # Create price_alerts table
    op.create_table(
        'price_alerts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('dispensary_id', sa.String(), nullable=False),
        sa.Column('alert_type', sa.String(), nullable=False),
        sa.Column('previous_price', sa.Float(), nullable=True),
        sa.Column('new_price', sa.Float(), nullable=True),
        sa.Column('percent_change', sa.Float(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('email_sent', sa.Boolean(), nullable=True, server_default='0'),
        sa.ForeignKeyConstraint(['dispensary_id'], ['dispensaries.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_price_alerts_alert_type'), 'price_alerts', ['alert_type'], unique=False)
    op.create_index(op.f('ix_price_alerts_dispensary_id'), 'price_alerts', ['dispensary_id'], unique=False)
    op.create_index(op.f('ix_price_alerts_product_id'), 'price_alerts', ['product_id'], unique=False)
    op.create_index(op.f('ix_price_alerts_sent_at'), 'price_alerts', ['sent_at'], unique=False)
    op.create_index(op.f('ix_price_alerts_user_id'), 'price_alerts', ['user_id'], unique=False)

    # Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('email_stock_alerts', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('email_price_drops', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('email_frequency', sa.String(), nullable=True, server_default="'immediately'"),
        sa.Column('app_notifications', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_preferences_user_id'), 'notification_preferences', ['user_id'], unique=True)


def downgrade() -> None:
    # Drop notification_preferences table
    op.drop_index(op.f('ix_notification_preferences_user_id'), table_name='notification_preferences')
    op.drop_table('notification_preferences')

    # Drop price_alerts table
    op.drop_index(op.f('ix_price_alerts_user_id'), table_name='price_alerts')
    op.drop_index(op.f('ix_price_alerts_sent_at'), table_name='price_alerts')
    op.drop_index(op.f('ix_price_alerts_product_id'), table_name='price_alerts')
    op.drop_index(op.f('ix_price_alerts_dispensary_id'), table_name='price_alerts')
    op.drop_index(op.f('ix_price_alerts_alert_type'), table_name='price_alerts')
    op.drop_table('price_alerts')

    # Drop watchlists table
    op.drop_index(op.f('ix_watchlists_user_id'), table_name='watchlists')
    op.drop_index(op.f('ix_watchlists_product_id'), table_name='watchlists')
    op.drop_table('watchlists')
