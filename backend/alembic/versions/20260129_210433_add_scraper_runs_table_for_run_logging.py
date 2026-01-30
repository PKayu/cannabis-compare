"""Add scraper_runs table for run logging

Revision ID: d61ee6846ddf
Revises: 5d1e45e38b68
Create Date: 2026-01-29 21:04:33.646030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd61ee6846ddf'
down_revision: Union[str, None] = '5d1e45e38b68'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create scraper_runs table
    op.create_table('scraper_runs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('scraper_id', sa.String(), nullable=False),
    sa.Column('scraper_name', sa.String(), nullable=False),
    sa.Column('dispensary_id', sa.String(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('duration_seconds', sa.Float(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('products_found', sa.Integer(), nullable=True),
    sa.Column('products_processed', sa.Integer(), nullable=True),
    sa.Column('flags_created', sa.Integer(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('error_type', sa.String(), nullable=True),
    sa.Column('retry_count', sa.Integer(), nullable=True),
    sa.Column('triggered_by', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['dispensary_id'], ['dispensaries.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scraper_runs_dispensary_id'), 'scraper_runs', ['dispensary_id'], unique=False)
    op.create_index(op.f('ix_scraper_runs_scraper_id'), 'scraper_runs', ['scraper_id'], unique=False)
    op.create_index(op.f('ix_scraper_runs_started_at'), 'scraper_runs', ['started_at'], unique=False)
    op.create_index(op.f('ix_scraper_runs_status'), 'scraper_runs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_scraper_runs_status'), table_name='scraper_runs')
    op.drop_index(op.f('ix_scraper_runs_started_at'), table_name='scraper_runs')
    op.drop_index(op.f('ix_scraper_runs_scraper_id'), table_name='scraper_runs')
    op.drop_index(op.f('ix_scraper_runs_dispensary_id'), table_name='scraper_runs')
    op.drop_table('scraper_runs')
