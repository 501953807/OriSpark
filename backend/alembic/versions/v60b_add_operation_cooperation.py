"""v6.0b: 新增 OperationCooperation 表."""

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table(
        'operation_cooperations',
        sa.Column('id', sa.String(length=32), primary_key=True),
        sa.Column('work_id', sa.String(length=32), nullable=False),
        sa.Column('operator_id', sa.String(length=32), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('creator_id', sa.String(length=32), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contract_id', sa.String(length=32), nullable=True),
        sa.Column('scope', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('operator_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_oc_operator', 'operation_cooperations', ['operator_id', 'status'])
    op.create_index('idx_oc_creator', 'operation_cooperations', ['creator_id', 'status'])
    op.create_index('idx_oc_work', 'operation_cooperations', ['work_id'])
    op.create_index('idx_oc_contract', 'operation_cooperations', ['contract_id'])


def downgrade() -> None:
    op.drop_index('idx_oc_contract', table_name='operation_cooperations')
    op.drop_index('idx_oc_work', table_name='operation_cooperations')
    op.drop_index('idx_oc_creator', table_name='operation_cooperations')
    op.drop_index('idx_oc_operator', table_name='operation_cooperations')
    op.drop_table('operation_cooperations')
