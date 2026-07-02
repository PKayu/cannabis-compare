"""add_is_admin_to_users

Revision ID: 548777494dfe
Revises: f2a3b4c5d6e7
Create Date: 2026-04-10 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError


revision: str = '548777494dfe'
down_revision: Union[str, None] = 'f2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        op.add_column(
            'users',
            sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false')
        )
    except OperationalError:
        pass  # Column already exists


def downgrade() -> None:
    try:
        op.drop_column('users', 'is_admin')
    except OperationalError:
        pass
