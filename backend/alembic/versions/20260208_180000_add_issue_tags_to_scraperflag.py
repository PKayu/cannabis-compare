"""Add issue_tags to ScraperFlag model

Revision ID: c3d4e5f6a7b8
Revises: ebbd80d0b601
Create Date: 2026-02-08 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'ebbd80d0b601'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('scraper_flags', sa.Column('issue_tags', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('scraper_flags', 'issue_tags')
