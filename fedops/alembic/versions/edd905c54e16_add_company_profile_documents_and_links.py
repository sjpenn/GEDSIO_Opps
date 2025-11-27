"""add_company_profile_documents_and_links

Revision ID: edd905c54e16
Revises: 51c483864494
Create Date: 2025-11-26 18:00:12.112384

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'edd905c54e16'
down_revision: Union[str, None] = '51c483864494'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add entity_uei column to company_profiles
    op.add_column('company_profiles', sa.Column('entity_uei', sa.String(), nullable=True))
    op.create_index(op.f('ix_company_profiles_entity_uei'), 'company_profiles', ['entity_uei'], unique=False)
    op.create_foreign_key('fk_company_profiles_entity_uei', 'company_profiles', 'entities', ['entity_uei'], ['uei'])
    
    # Create company_profile_documents table
    op.create_table('company_profile_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_uei', sa.String(), nullable=False),
        sa.Column('document_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_uei'], ['company_profiles.uei'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_company_profile_documents_company_uei'), 'company_profile_documents', ['company_uei'], unique=False)
    op.create_index(op.f('ix_company_profile_documents_document_type'), 'company_profile_documents', ['document_type'], unique=False)
    op.create_index(op.f('ix_company_profile_documents_id'), 'company_profile_documents', ['id'], unique=False)
    
    # Create company_profile_links table
    op.create_table('company_profile_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_uei', sa.String(), nullable=False),
        sa.Column('link_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_uei'], ['company_profiles.uei'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_company_profile_links_company_uei'), 'company_profile_links', ['company_uei'], unique=False)
    op.create_index(op.f('ix_company_profile_links_id'), 'company_profile_links', ['id'], unique=False)
    op.create_index(op.f('ix_company_profile_links_link_type'), 'company_profile_links', ['link_type'], unique=False)


def downgrade() -> None:
    # Drop company_profile_links table
    op.drop_index(op.f('ix_company_profile_links_link_type'), table_name='company_profile_links')
    op.drop_index(op.f('ix_company_profile_links_id'), table_name='company_profile_links')
    op.drop_index(op.f('ix_company_profile_links_company_uei'), table_name='company_profile_links')
    op.drop_table('company_profile_links')
    
    # Drop company_profile_documents table
    op.drop_index(op.f('ix_company_profile_documents_id'), table_name='company_profile_documents')
    op.drop_index(op.f('ix_company_profile_documents_document_type'), table_name='company_profile_documents')
    op.drop_index(op.f('ix_company_profile_documents_company_uei'), table_name='company_profile_documents')
    op.drop_table('company_profile_documents')
    
    # Remove entity_uei column from company_profiles
    op.drop_constraint('fk_company_profiles_entity_uei', 'company_profiles', type_='foreignkey')
    op.drop_index(op.f('ix_company_profiles_entity_uei'), table_name='company_profiles')
    op.drop_column('company_profiles', 'entity_uei')

