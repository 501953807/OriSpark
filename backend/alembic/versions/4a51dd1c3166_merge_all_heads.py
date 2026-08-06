"""merge_all_heads

Revision ID: 4a51dd1c3166
Revises: 4e4d7d398876, e001_enforcement_operator_id
Create Date: 2026-08-04 23:49:30.720814
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '4a51dd1c3166'
down_revision: Union[str, None] = ('4e4d7d398876', 'e001_enforcement_operator_id')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
