"""add_requirement_tracking_tables

Revision ID: 664fba81bb6f
Revises: 1bac2dc93831
Create Date: 2025-11-27 11:24:15.541134

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '664fba81bb6f'
down_revision: Union[str, None] = '1bac2dc93831'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create proposal_requirements table
    op.create_table(
        'proposal_requirements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('proposal_id', sa.Integer(), nullable=False),
        sa.Column('requirement_text', sa.Text(), nullable=False),
        sa.Column('requirement_type', sa.String(), nullable=False),  # TECHNICAL, MANAGEMENT, PAST_PERFORMANCE, PRICING, CERTIFICATION, OTHER
        sa.Column('source_document_id', sa.Integer(), nullable=True),
        sa.Column('source_section', sa.String(), nullable=True),
        sa.Column('source_location', sa.JSON(), nullable=True),  # {page, paragraph, start_char, end_char}
        sa.Column('priority', sa.String(), nullable=False, server_default='IMPORTANT'),  # MANDATORY, IMPORTANT, OPTIONAL
        sa.Column('compliance_status', sa.String(), nullable=False, server_default='NOT_STARTED'),  # NOT_STARTED, IN_PROGRESS, COMPLETE, REVIEWED
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['proposal_id'], ['proposals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_document_id'], ['stored_files.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_proposal_requirements_proposal_id', 'proposal_requirements', ['proposal_id'])
    op.create_index('ix_proposal_requirements_type', 'proposal_requirements', ['requirement_type'])
    op.create_index('ix_proposal_requirements_status', 'proposal_requirements', ['compliance_status'])
    
    # Create requirement_responses table
    op.create_table(
        'requirement_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requirement_id', sa.Integer(), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('proposal_section_ref', sa.String(), nullable=True),
        sa.Column('assigned_to', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='DRAFT'),  # DRAFT, REVIEW, APPROVED
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['requirement_id'], ['proposal_requirements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_requirement_responses_requirement_id', 'requirement_responses', ['requirement_id'])
    
    # Create document_artifacts table
    op.create_table(
        'document_artifacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('proposal_id', sa.Integer(), nullable=False),
        sa.Column('artifact_type', sa.String(), nullable=False),  # FORM, CERTIFICATION, PAST_PERFORMANCE, PRICING_SHEET, OTHER
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_section', sa.String(), nullable=True),
        sa.Column('required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('status', sa.String(), nullable=False, server_default='NOT_STARTED'),  # NOT_STARTED, IN_PROGRESS, COMPLETE
        sa.Column('file_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['proposal_id'], ['proposals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['file_id'], ['stored_files.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_document_artifacts_proposal_id', 'document_artifacts', ['proposal_id'])
    op.create_index('ix_document_artifacts_type', 'document_artifacts', ['artifact_type'])


def downgrade() -> None:
    op.drop_index('ix_document_artifacts_type', table_name='document_artifacts')
    op.drop_index('ix_document_artifacts_proposal_id', table_name='document_artifacts')
    op.drop_table('document_artifacts')
    
    op.drop_index('ix_requirement_responses_requirement_id', table_name='requirement_responses')
    op.drop_table('requirement_responses')
    
    op.drop_index('ix_proposal_requirements_status', table_name='proposal_requirements')
    op.drop_index('ix_proposal_requirements_type', table_name='proposal_requirements')
    op.drop_index('ix_proposal_requirements_proposal_id', table_name='proposal_requirements')
    op.drop_table('proposal_requirements')

