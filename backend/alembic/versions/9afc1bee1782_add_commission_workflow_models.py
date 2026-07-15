"""add commission workflow models

Revision ID: 9afc1bee1782
Revises: e34135f4e811
Create Date: 2026-06-30 17:21:12.792448
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '9afc1bee1782'
down_revision: Union[str, None] = 'e34135f4e811'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop legacy JSON milestones column from commission_projects
    with op.batch_alter_table('commission_projects') as batch_op:
        batch_op.drop_column('milestones')


def downgrade() -> None:
    with op.batch_alter_table('commission_projects') as batch_op:
        batch_op.add_column(sa.Column('milestones', sa.JSON(), nullable=True))
