"""merge logistics and previous heads

Revision ID: f07708b3b832
Revises: f7e8d9c0b1a2, 80aa210070a4
Create Date: 2026-07-21 16:27:31.775791
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f07708b3b832'
down_revision: Union[str, None] = ('f7e8d9c0b1a2', '80aa210070a4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
