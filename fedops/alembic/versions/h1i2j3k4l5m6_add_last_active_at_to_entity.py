"""Add last_active_at to entity for multi-entity switching

Revision ID: h1i2j3k4l5m6
Revises: g8h9i0j1k2l3
Create Date: 2024-12-16 14:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h1i2j3k4l5m6'
down_revision: Union[str, None] = 'g8h9i0j1k2l3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add last_active_at column to entities table
    op.add_column('entities', sa.Column('last_active_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('entities', 'last_active_at')
