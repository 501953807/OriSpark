"""add innocence_proof_table

Revision ID: 4604a118aca7
Revises: g8f9e0d1c2b3
Create Date: 2026-07-28 20:27:06.546169
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '4604a118aca7'
down_revision: Union[str, None] = 'g8f9e0d1c2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
