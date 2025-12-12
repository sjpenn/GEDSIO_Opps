"""add_past_performance_table

Revision ID: ee47ce435664
Revises: 72492b0c79a8
Create Date: 2025-12-11 18:13:43.335540

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'ee47ce435664'
down_revision: Union[str, None] = '72492b0c79a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'past_performances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_uei', sa.String(), nullable=False),
        sa.Column('award_id', sa.String(), nullable=True),
        sa.Column('opportunity_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='DRAFT'),
        sa.Column('questionnaire_data', JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['entity_uei'], ['entities.uei'], ),
        sa.ForeignKeyConstraint(['award_id'], ['entity_awards.award_id'], ),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_past_performances_entity_uei'), 'past_performances', ['entity_uei'], unique=False)
    op.create_index(op.f('ix_past_performances_award_id'), 'past_performances', ['award_id'], unique=False)
    op.create_index(op.f('ix_past_performances_opportunity_id'), 'past_performances', ['opportunity_id'], unique=False)
    op.create_index(op.f('ix_past_performances_status'), 'past_performances', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_past_performances_status'), table_name='past_performances')
    op.drop_index(op.f('ix_past_performances_opportunity_id'), table_name='past_performances')
    op.drop_index(op.f('ix_past_performances_award_id'), table_name='past_performances')
    op.drop_index(op.f('ix_past_performances_entity_uei'), table_name='past_performances')
    op.drop_table('past_performances')

