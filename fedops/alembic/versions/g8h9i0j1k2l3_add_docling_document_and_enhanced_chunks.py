"""Add docling document and enhanced chunks

Revision ID: g8h9i0j1k2l3
Revises: a1b2c3d4e5f6
Create Date: 2024-12-16 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'g8h9i0j1k2l3'
down_revision: Union[str, None] = 'eb45098e4e3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to document_chunks table
    op.add_column('document_chunks', sa.Column('opportunity_id', sa.Integer(), nullable=True))
    op.add_column('document_chunks', sa.Column('start_position', sa.Integer(), nullable=True))
    op.add_column('document_chunks', sa.Column('end_position', sa.Integer(), nullable=True))
    op.add_column('document_chunks', sa.Column('chunk_type', sa.String(), nullable=True))
    op.add_column('document_chunks', sa.Column('heading_context', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('document_chunks', sa.Column('vector_id', sa.String(), nullable=True))
    
    # Create indexes for new columns
    op.create_index(op.f('ix_document_chunks_opportunity_id'), 'document_chunks', ['opportunity_id'], unique=False)
    op.create_index(op.f('ix_document_chunks_vector_id'), 'document_chunks', ['vector_id'], unique=False)
    
    # Create foreign key for opportunity_id
    op.create_foreign_key(
        'fk_document_chunks_opportunity_id',
        'document_chunks',
        'opportunities',
        ['opportunity_id'],
        ['id']
    )
    
    # Create docling_documents table
    op.create_table('docling_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stored_file_id', sa.Integer(), nullable=False),
        sa.Column('opportunity_id', sa.Integer(), nullable=False),
        sa.Column('docling_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('markdown', sa.Text(), nullable=True),
        sa.Column('num_pages', sa.Integer(), nullable=True),
        sa.Column('num_tables', sa.Integer(), nullable=True),
        sa.Column('num_chunks', sa.Integer(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ),
        sa.ForeignKeyConstraint(['stored_file_id'], ['stored_files.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_docling_documents_id'), 'docling_documents', ['id'], unique=False)
    op.create_index(op.f('ix_docling_documents_opportunity_id'), 'docling_documents', ['opportunity_id'], unique=False)
    op.create_index(op.f('ix_docling_documents_stored_file_id'), 'docling_documents', ['stored_file_id'], unique=True)


def downgrade() -> None:
    # Drop docling_documents table
    op.drop_index(op.f('ix_docling_documents_stored_file_id'), table_name='docling_documents')
    op.drop_index(op.f('ix_docling_documents_opportunity_id'), table_name='docling_documents')
    op.drop_index(op.f('ix_docling_documents_id'), table_name='docling_documents')
    op.drop_table('docling_documents')
    
    # Remove new columns from document_chunks
    op.drop_constraint('fk_document_chunks_opportunity_id', 'document_chunks', type_='foreignkey')
    op.drop_index(op.f('ix_document_chunks_vector_id'), table_name='document_chunks')
    op.drop_index(op.f('ix_document_chunks_opportunity_id'), table_name='document_chunks')
    op.drop_column('document_chunks', 'vector_id')
    op.drop_column('document_chunks', 'heading_context')
    op.drop_column('document_chunks', 'chunk_type')
    op.drop_column('document_chunks', 'end_position')
    op.drop_column('document_chunks', 'start_position')
    op.drop_column('document_chunks', 'opportunity_id')
