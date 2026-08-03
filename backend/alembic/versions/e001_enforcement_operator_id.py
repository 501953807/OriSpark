"""enforcement_actions - Add operator_id column.

Revision ID: e001_enforcement_operator_id
Revises: wmk_preset_1
Create Date: 2026-08-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e001_enforcement_operator_id'
down_revision = 'wmk_preset_1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('enforcement_actions',
        sa.Column('operator_id', sa.String(length=32), nullable=True)
    )
    op.create_index('idx_enforcement_action_operator', 'enforcement_actions', ['operator_id'])


def downgrade():
    op.drop_index('idx_enforcement_action_operator', table_name='enforcement_actions')
    op.drop_column('enforcement_actions', 'operator_id')
