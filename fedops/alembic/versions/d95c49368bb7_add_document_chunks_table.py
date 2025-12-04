"""add document chunks table

Revision ID: d95c49368bb7
Revises: 54fa025e2e46
Create Date: 2025-11-30 08:47:30.123456

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd95c49368bb7'
down_revision = '54fa025e2e46'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('document_chunks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('stored_file_id', sa.Integer(), nullable=False),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['stored_file_id'], ['stored_files.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_chunks_id'), 'document_chunks', ['id'], unique=False)
    op.create_index(op.f('ix_document_chunks_stored_file_id'), 'document_chunks', ['stored_file_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_document_chunks_stored_file_id'), table_name='document_chunks')
    op.drop_index(op.f('ix_document_chunks_id'), table_name='document_chunks')
    op.drop_table('document_chunks')
