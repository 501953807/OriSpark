"""add_creator_id_to_works

Revision ID: 2b99b46248ca
Revises: g8f9e0d1c2b3
Create Date: 2026-07-28 00:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import logging
import time

logger = logging.getLogger(__name__)

revision: str = '2b99b46248ca'
down_revision: Union[str, None] = 'g8f9e0d1c2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _safe_create_index(idx_name: str, table_name: str, columns: list, unique: bool = False) -> None:
    """Create index only if it does not exist (SQLite compatible)."""
    conn = op.get_bind()
    existing = conn.execute(
        sa.text(f"SELECT name FROM sqlite_master WHERE type='index' AND name=:idx AND tbl_name=:tbl"),
        {"idx": idx_name, "tbl": table_name}
    ).fetchone()
    if existing:
        return
    op.create_index(idx_name, table_name, columns, unique=unique)


def _safe_drop_index(idx_name: str, table_name: str) -> None:
    """Drop index if it exists."""
    conn = op.get_bind()
    existing = conn.execute(
        sa.text(f"SELECT name FROM sqlite_master WHERE type='index' AND name=:idx AND tbl_name=:tbl"),
        {"idx": idx_name, "tbl": table_name}
    ).fetchone()
    if not existing:
        return
    op.drop_index(idx_name, table_name=table_name)


def upgrade() -> None:
    """Add creator_id column to works table with foreign key to users."""
    # Check if column already exists
    conn = op.get_bind()
    rows = conn.execute(sa.text("PRAGMA table_info(works)")).fetchall()
    col_names = {r[1] for r in rows}

    if 'creator_id' not in col_names:
        # Add the creator_id column (nullable initially)
        with op.batch_alter_table('works', schema=None) as batch_op:
            batch_op.add_column(sa.Column('creator_id', sa.String(length=32), nullable=True))

        # Create foreign key constraint after column exists
        with op.batch_alter_table('works', schema=None) as batch_op:
            batch_op.create_foreign_key(
                'fk_works_creator_id', 'users', ['creator_id'], ['id'],
                ondelete='CASCADE'
            )

        # Create index for creator_id
        _safe_create_index('idx_works_creator', 'works', ['creator_id'])
    else:
        logger.info("creator_id column already exists in works table")

    # Verify column was added
    cols = conn.execute(sa.text("PRAGMA table_info(works)")).fetchall()
    col_names_post = [c[1] for c in cols]
    if 'creator_id' not in col_names_post:
        logger.warning("creator_id column missing after upgrade operation")


def downgrade() -> None:
    """Remove creator_id column from works table."""
    # Drop the index first
    _safe_drop_index('idx_works_creator', 'works')

    # Drop the foreign key constraint
    try:
        with op.batch_alter_table('works', schema=None) as batch_op:
            batch_op.drop_constraint('fk_works_creator_id', type_='foreignkey')
    except Exception as e:
        logger.warning(f"Could not drop FK constraint: {e}")

    # Drop the column
    try:
        with op.batch_alter_table('works', schema=None) as batch_op:
            batch_op.drop_column('creator_id')
    except Exception as e:
        logger.warning(f"Could not drop column: {e}")