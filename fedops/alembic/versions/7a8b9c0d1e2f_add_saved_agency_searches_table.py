"""add saved agency searches table

Revision ID: 7a8b9c0d1e2f
Revises: a4ca44385ced
Create Date: 2024-12-11 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '7a8b9c0d1e2f'
down_revision = 'a4ca44385ced'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('saved_agency_searches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agency_name', sa.String(), nullable=False),
        sa.Column('acronym', sa.String(), nullable=True),
        sa.Column('icon_type', sa.String(), nullable=True),
        sa.Column('overview', sa.Text(), nullable=True),
        sa.Column('strategic_goals', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('budget_outlook', sa.Text(), nullable=True),
        sa.Column('org_structure', sa.Text(), nullable=True),
        sa.Column('org_tree', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('key_bureaus', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('lines_of_business', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('budget_by_division', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('pain_points', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('procurement_priorities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('raw_response', sa.Text(), nullable=True),
        sa.Column('last_refreshed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_saved_agency_searches_agency_name'), 'saved_agency_searches', ['agency_name'], unique=False)
    op.create_index(op.f('ix_saved_agency_searches_id'), 'saved_agency_searches', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_saved_agency_searches_id'), table_name='saved_agency_searches')
    op.drop_index(op.f('ix_saved_agency_searches_agency_name'), table_name='saved_agency_searches')
    op.drop_table('saved_agency_searches')
