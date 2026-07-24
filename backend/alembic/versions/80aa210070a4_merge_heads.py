"""merge heads

Revision ID: 80aa210070a4
Revises: d62359dbdd00, a1b2c3d4e5f6
Create Date: 2026-07-21 16:18:55.921513
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '80aa210070a4'
down_revision: Union[str, None] = ('d62359dbdd00', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
