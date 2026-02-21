"""add flag_type column to scraper_flags

Adds flag_type to distinguish between legacy match_review flags
and new data_cleanup flags. All existing rows default to match_review.

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-02-20 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'scraper_flags',
        sa.Column('flag_type', sa.String(), nullable=True, server_default='match_review')
    )
    op.create_index('ix_scraper_flags_flag_type', 'scraper_flags', ['flag_type'])
    # Backfill all existing rows
    op.execute("UPDATE scraper_flags SET flag_type = 'match_review' WHERE flag_type IS NULL")


def downgrade() -> None:
    op.drop_index('ix_scraper_flags_flag_type', table_name='scraper_flags')
    op.drop_column('scraper_flags', 'flag_type')
