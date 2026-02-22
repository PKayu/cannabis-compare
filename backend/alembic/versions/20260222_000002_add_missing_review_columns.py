"""add_missing_review_columns

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-02-22 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError


revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _safe_add_column(table, column):
    try:
        op.add_column(table, column)
    except OperationalError:
        pass  # Column already exists


def upgrade() -> None:
    """Add columns missing from reviews table (intention_type, intention_tag, batch_number, cultivation_date, updated_at)"""
    _safe_add_column('reviews', sa.Column('intention_type', sa.String(), nullable=True))
    _safe_add_column('reviews', sa.Column('intention_tag', sa.String(), nullable=True))
    _safe_add_column('reviews', sa.Column('batch_number', sa.String(), nullable=True))
    _safe_add_column('reviews', sa.Column('cultivation_date', sa.DateTime(), nullable=True))
    _safe_add_column('reviews', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('reviews', 'updated_at')
    op.drop_column('reviews', 'cultivation_date')
    op.drop_column('reviews', 'batch_number')
    op.drop_column('reviews', 'intention_tag')
    op.drop_column('reviews', 'intention_type')
