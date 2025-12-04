"""add chunk metadata

Revision ID: f6a74aaee1ef
Revises: d95c49368bb7
Create Date: 2025-11-30 09:00:00.123456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6a74aaee1ef'
down_revision = 'd95c49368bb7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('document_chunks', sa.Column('page_number', sa.Integer(), nullable=True))
    op.add_column('document_chunks', sa.Column('section', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('document_chunks', 'section')
    op.drop_column('document_chunks', 'page_number')
