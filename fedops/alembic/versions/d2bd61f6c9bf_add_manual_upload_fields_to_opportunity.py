"""add_manual_upload_fields_to_opportunity

Revision ID: d2bd61f6c9bf
Revises: f38e8e5cf21c
Create Date: 2025-12-01 09:45:48.093045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2bd61f6c9bf'
down_revision: Union[str, None] = 'f38e8e5cf21c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use raw SQL to check and add columns only if they don't exist
    conn = op.get_bind()
    
    # Check if source column exists
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name='opportunities' AND column_name='source'"
    ))
    if not result.fetchone():
        op.add_column('opportunities', sa.Column('source', sa.String(), nullable=True, server_default='SAM.gov'))
    
    # Check and add incumbent fields
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name='opportunities' AND column_name='incumbent_vendor'"
    ))
    if not result.fetchone():
        op.add_column('opportunities', sa.Column('incumbent_vendor', sa.String(), nullable=True))
        op.add_column('opportunities', sa.Column('incumbent_contract_number', sa.String(), nullable=True))
        op.add_column('opportunities', sa.Column('incumbent_value', sa.String(), nullable=True))
        op.add_column('opportunities', sa.Column('incumbent_expiration_date', sa.DateTime(), nullable=True))
        op.add_column('opportunities', sa.Column('previous_sow_document_id', sa.Integer(), nullable=True))
        
        # Add foreign key constraint for previous_sow_document_id
        op.create_foreign_key(
            'fk_opportunities_previous_sow_document_id',
            'opportunities', 'stored_files',
            ['previous_sow_document_id'], ['id']
        )


def downgrade() -> None:
    # Check if constraint exists before dropping
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT constraint_name FROM information_schema.table_constraints WHERE table_name='opportunities' AND constraint_name='fk_opportunities_previous_sow_document_id'"
    ))
    if result.fetchone():
        op.drop_constraint('fk_opportunities_previous_sow_document_id', 'opportunities', type_='foreignkey')
    
    # Drop columns if they exist
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name='opportunities' AND column_name='previous_sow_document_id'"
    ))
    if result.fetchone():
        op.drop_column('opportunities', 'previous_sow_document_id')
        op.drop_column('opportunities', 'incumbent_expiration_date')
        op.drop_column('opportunities', 'incumbent_value')
        op.drop_column('opportunities', 'incumbent_contract_number')
        op.drop_column('opportunities', 'incumbent_vendor')
    
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name='opportunities' AND column_name='source'"
    ))
    if result.fetchone():
        op.drop_column('opportunities', 'source')
