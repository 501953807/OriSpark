"""v6.0: add login_platform to User

Revision ID: v60a_add_login_platform
Revises: wmk_preset_1_add_watermark_preset_table
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa

revision = 'v60a_add_login_platform'
down_revision = 'wmk_preset_1_add_watermark_preset_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('login_platform', sa.String(length=20), nullable=True, server_default='web'))


def downgrade() -> None:
    op.drop_column('users', 'login_platform')
