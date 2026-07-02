"""Add product_url to Price model

Revision ID: 2581cbbc6411
Revises: a1b2c3d4e5f6
Create Date: 2026-02-08 11:56:32.457864

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2581cbbc6411'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('prices', sa.Column('product_url', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('prices', 'product_url')
