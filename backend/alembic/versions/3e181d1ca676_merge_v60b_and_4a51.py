"""merge_v60b_and_4a51

Revision ID: 3e181d1ca676
Revises: 4a51dd1c3166, v60b_add_operation_cooperation
Create Date: 2026-08-11 00:36:14.013031
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '3e181d1ca676'
down_revision: Union[str, None] = ('4a51dd1c3166', 'v60b_add_operation_cooperation')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
