"""merge_heads

Revision ID: 72492b0c79a8
Revises: 60666958a0ec, 7a8b9c0d1e2f
Create Date: 2025-12-11 18:13:37.840513

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '72492b0c79a8'
down_revision: Union[str, None] = ('60666958a0ec', '7a8b9c0d1e2f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
