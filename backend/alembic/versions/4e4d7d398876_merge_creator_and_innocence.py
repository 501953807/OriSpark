"""merge_creator_and_innocence

Revision ID: 4e4d7d398876
Revises: 2b99b46248ca, 4604a118aca7
Create Date: 2026-08-04 23:46:21.743640
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '4e4d7d398876'
down_revision: Union[str, None] = ('2b99b46248ca', '4604a118aca7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
