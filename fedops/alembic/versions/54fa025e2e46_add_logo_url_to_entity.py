"""add logo_url to entity

Revision ID: 54fa025e2e46
Revises: 00dc3fd655db
Create Date: 2025-11-29 16:01:08.446860

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54fa025e2e46'
down_revision: Union[str, None] = '00dc3fd655db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('entities', sa.Column('logo_url', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('entities', 'logo_url')
