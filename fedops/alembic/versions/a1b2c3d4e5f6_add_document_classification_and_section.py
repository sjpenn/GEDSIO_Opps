"""add document classification and section tables

Revision ID: a1b2c3d4e5f6
Revises: ee47ce435664
Create Date: 2025-12-14 13:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'ee47ce435664'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Document classification tracking
    op.create_table(
        'document_classifications',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('opportunity_id', sa.Integer(), sa.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('classification_type', sa.String(20), nullable=False),  # SINGLE_DOCUMENT, MULTI_DOCUMENT, HYBRID
        sa.Column('confidence', sa.String(10), nullable=False),  # HIGH, MEDIUM, LOW
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('document_inventory', JSONB, nullable=True),  # Detailed inventory of all files
        sa.Column('extraction_strategy', JSONB, nullable=True),  # How to process documents
        sa.Column('amendment_count', sa.Integer(), server_default='0'),  # Number of amendments detected
        sa.Column('amendment_files', JSONB, nullable=True),  # List of amendment filenames
        sa.Column('base_document_files', JSONB, nullable=True),  # List of base document filenames
        sa.Column('critical_sections', JSONB, nullable=True),  # ["L", "M", "C"]
        sa.Column('classified_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    op.create_index('idx_doc_class_opp_id', 'document_classifications', ['opportunity_id'])
    op.create_index('idx_doc_class_type', 'document_classifications', ['classification_type'])
    
    # Parsed section boundaries
    op.create_table(
        'document_sections',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('stored_file_id', sa.Integer(), sa.ForeignKey('stored_files.id', ondelete='CASCADE'), nullable=False),
        sa.Column('opportunity_id', sa.Integer(), sa.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_letter', sa.String(2), nullable=False),  # A, B, C, ... M, or custom
        sa.Column('section_title', sa.String(500), nullable=True),
        sa.Column('start_position', sa.Integer(), nullable=True),  # Character position start
        sa.Column('end_position', sa.Integer(), nullable=True),  # Character position end
        sa.Column('start_line', sa.Integer(), nullable=True),  # Line number start
        sa.Column('end_line', sa.Integer(), nullable=True),  # Line number end
        sa.Column('confidence_level', sa.String(10), nullable=True),  # HIGH, MEDIUM, LOW
        sa.Column('detection_method', sa.String(50), nullable=True),  # explicit_header, inferred, cross_reference
        sa.Column('content', sa.Text(), nullable=True),  # Extracted section content
        sa.Column('metadata', JSONB, nullable=True),  # Additional structured data
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('stored_file_id', 'section_letter', name='uq_file_section'),
    )
    
    op.create_index('idx_doc_sections_opp', 'document_sections', ['opportunity_id'])
    op.create_index('idx_doc_sections_file', 'document_sections', ['stored_file_id'])
    op.create_index('idx_doc_sections_letter', 'document_sections', ['section_letter'])
    
    # AI-generated section summaries
    op.create_table(
        'section_summaries',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('section_id', sa.Integer(), sa.ForeignKey('document_sections.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('key_findings', JSONB, nullable=True),  # Array of key findings
        sa.Column('proposal_implications', sa.Text(), nullable=True),  # How to address in proposal
        sa.Column('red_flags', JSONB, nullable=True),  # Array of risks/concerns
        sa.Column('opportunities', JSONB, nullable=True),  # Array of differentiators
        sa.Column('questions_to_ask', JSONB, nullable=True),  # Clarification questions
        sa.Column('generated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('model_used', sa.String(100), nullable=True),
    )
    
    op.create_index('idx_section_summaries_section', 'section_summaries', ['section_id'])
    
    # Extracted requirements (detailed extraction from sections)
    op.create_table(
        'extracted_requirements',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('section_id', sa.Integer(), sa.ForeignKey('document_sections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('opportunity_id', sa.Integer(), sa.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requirement_id', sa.String(50), nullable=True),  # e.g., C_156_1
        sa.Column('requirement_text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=True),  # FUNCTIONAL, TECHNICAL, COMPLIANCE, etc.
        sa.Column('compliance_level', sa.String(20), nullable=True),  # MANDATORY, CONDITIONAL, OPTIONAL
        sa.Column('key_metrics', JSONB, nullable=True),  # {metric_name: value}
        sa.Column('dependencies', JSONB, nullable=True),  # Array of related requirement IDs
        sa.Column('cross_references', JSONB, nullable=True),  # Links to other sections
        sa.Column('proposal_impact', sa.Text(), nullable=True),
        sa.Column('source_quote', sa.Text(), nullable=True),  # Original text from document
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    op.create_index('idx_ext_requirements_section', 'extracted_requirements', ['section_id'])
    op.create_index('idx_ext_requirements_opp', 'extracted_requirements', ['opportunity_id'])
    op.create_index('idx_ext_requirements_category', 'extracted_requirements', ['category'])
    
    # Evaluation criteria to requirements mapping
    op.create_table(
        'evaluation_mappings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('opportunity_id', sa.Integer(), sa.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('evaluation_factor', sa.String(300), nullable=False),
        sa.Column('weight_percent', sa.Integer(), nullable=True),
        sa.Column('scoring_description', sa.Text(), nullable=True),
        sa.Column('critical_success_factors', JSONB, nullable=True),  # Array of CSFs
        sa.Column('related_requirement_ids', JSONB, nullable=True),  # Array of requirement IDs
        sa.Column('proposal_strategy', sa.Text(), nullable=True),
        sa.Column('source_section', sa.String(10), nullable=True),  # Usually "M"
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    op.create_index('idx_eval_mapping_opp', 'evaluation_mappings', ['opportunity_id'])


def downgrade() -> None:
    op.drop_table('evaluation_mappings')
    op.drop_table('extracted_requirements')
    op.drop_table('section_summaries')
    op.drop_table('document_sections')
    op.drop_table('document_classifications')
