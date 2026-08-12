"""v6.0c: 为 works 表添加公开可运营状态字段.

revision: 'v60c_add_work_operation_public'
down_revision: '3e181d1ca676'  (当前 head)
"""

revision = 'v60c_add_work_operation_public'
down_revision = '3e181d1ca676'

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.add_column(
        'works',
        sa.Column('work_operation_public', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.add_column(
        'works',
        sa.Column('operation_agreement_id', sa.String(length=32), nullable=True),
    )
    op.create_index('idx_works_operation_public', 'works', ['work_operation_public'])


def downgrade() -> None:
    op.drop_index('idx_works_operation_public', table_name='works')
    op.drop_column('works', 'operation_agreement_id')
    op.drop_column('works', 'work_operation_public')
