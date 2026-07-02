"""add_new_tables

Revision ID: 59697f1647fd
Revises: 5e2337c33efd
Create Date: 2026-07-02 11:54:46.034641
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import logging

logger = logging.getLogger(__name__)

revision: str = '59697f1647fd'
down_revision: Union[str, None] = '5e2337c33efd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _safe_create_index(idx_name: str, table_name: str, columns: list, unique: bool = False) -> None:
    """Create index only if it does not already exist (SQLite compatible)."""
    conn = op.get_bind()
    existing = conn.execute(
        sa.text(f"SELECT name FROM sqlite_master WHERE type='index' AND name=:idx AND tbl_name=:tbl"),
        {"idx": idx_name, "tbl": table_name}
    ).fetchone()
    if existing:
        return
    op.create_index(idx_name, table_name, columns, unique=unique)


def _safe_add_column(table_name: str, col_name: str) -> bool:
    """Add a column if it does not exist. Returns True if added, False if skipped."""
    conn = op.get_bind()
    rows = conn.execute(sa.text(f"PRAGMA table_info({table_name})")).fetchall()
    col_names = {r[1] for r in rows} if rows else set()
    if col_name in col_names:
        return False
    return True


def _safe_drop_column(table_name: str, col_name: str) -> None:
    """Drop a column if it exists (SQLite: rebuild table)."""
    conn = op.get_bind()
    rows = conn.execute(sa.text(f"PRAGMA table_info({table_name})")).fetchall()
    col_names = {r[1] for r in rows} if rows else set()
    if col_name not in col_names:
        return
    _rebuild_table_drop_col(table_name, col_name)


def _rebuild_table_drop_col(table_name: str, drop_col: str) -> None:
    """Rebuild table excluding a single column (SQLite workaround)."""
    conn = op.get_bind()
    rows = conn.execute(sa.text(f"PRAGMA table_info({table_name})")).fetchall()
    col_defs = []
    fk_rows = conn.execute(sa.text(f"PRAGMA foreign_key_list({table_name})")).fetchall()

    selected = []
    for r in rows:
        if r[1] != drop_col:
            selected.append(r)

    if not selected:
        return  # cannot drop the last column

    # Find PK
    pk_col = None
    for r in rows:
        if r[5] == 1:  # PK flag
            pk_col = r[1]
            break

    col_str_parts = []
    for r in selected:
        cid, cname, ctype, notnull, dflt, pk = r
        line = f"  {cname} {ctype}"
        if notnull:
            line += " NOT NULL"
        if dflt is not None:
            line += f" DEFAULT {dflt}"
        if pk and pk_col:
            line += f" PRIMARY KEY"
        col_str_parts.append(line)

    # Foreign keys
    fk_strs = []
    for fk in fk_rows:
        fk_strs.append(
            f"FOREIGN KEY ({fk[3]}) REFERENCES {fk[2]}({fk[4]})"
        )

    all_cols = col_str_parts + fk_strs
    new_table = f"{table_name}_new"
    col_block = ",\n".join(all_cols)
    conn.execute(sa.text(f"DROP TABLE IF EXISTS {new_table}"))
    conn.execute(sa.text(f"CREATE TABLE {new_table} ({col_block})"))
    cols_keep = ", ".join(r[1] for r in selected)
    conn.execute(sa.text(f"INSERT INTO {new_table} ({cols_keep}) SELECT {cols_keep} FROM {table_name}"))
    conn.execute(sa.text(f"DROP TABLE {table_name}"))
    conn.execute(sa.text(f"ALTER TABLE {new_table} RENAME TO {table_name}"))
    # Recreate indices
    indices = conn.execute(sa.text(f"PRAGMA index_list({table_name})")).fetchall()
    for idx_info in indices:
        idx_name = idx_info[1]
        if idx_name.startswith('sqlite_'):
            continue
        idx_cols_raw = conn.execute(sa.text(f"PRAGMA index_info({idx_name})")).fetchall()
        idx_cols = ", ".join(c[2] for c in idx_cols_raw)
        unique = idx_info[2]
        conn.execute(sa.text(f"CREATE{' UNIQUE' if unique else ''} INDEX {idx_name} ON {table_name} ({idx_cols})"))

# Safe column helpers end here


def _safe_drop_index(idx_name: str, table_name: str) -> None:
    """Drop index if it exists."""
    conn = op.get_bind()
    existing = conn.execute(
        sa.text(f"SELECT name FROM sqlite_master WHERE type='index' AND name=:idx AND tbl_name=:tbl"),
        {"idx": idx_name, "tbl": table_name}
    ).fetchone()
    if existing:
        op.drop_index(idx_name, table_name=table_name)


def _safe_create_table_if_not_exists(table_name: str, sa_col_defs, sa_fk=None, sa_pk=None) -> None:
    """Create table only if it does not exist."""
    conn = op.get_bind()
    tables = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"), {"t": table_name}).fetchall()
    if tables:
        return
    op.create_table(table_name, *sa_col_defs, *(sa_fk or []), *(sa_pk or []))


SAFE_COL = sa.Column  # alias


def _alter_column_sqlite(table_name: str, col_name: str, new_type, nullable: bool = None) -> None:
    """SQLite does not support ALTER COLUMN. Workaround: rebuild the table."""
    conn = op.get_bind()
    rows = conn.execute(sa.text(f"PRAGMA table_info({table_name})")).fetchall()
    col_info = {r[1]: r for r in rows}
    if col_name not in col_info:
        return
    orig = col_info[col_name]
    orig_type = orig[2]
    if orig_type.lower().replace(' ', '') == str(new_type).lower().replace(' ', ''):
        # Already the same type, no change needed
        if nullable is not None and ((orig[3] == '0') != nullable):
            _set_nullable(table_name, col_name, nullable)
        return

    # Build column list with renamed type
    col_defs = []
    fk_defs = []
    for r in rows:
        cname, ctype, notnull = r[1], r[2], r[3]
        cid = r[0]
        if cname == col_name:
            ctype = str(new_type)
        col_defs.append(f"  {cname} {ctype}")
        if cid == orig[4]:  # PK
            col_defs[-1] += " PRIMARY KEY"

    # Get foreign keys
    fks = conn.execute(sa.text(f"PRAGMA foreign_key_list({table_name})")).fetchall()
    for fk in fks:
        fk_defs.append(f"FOREIGN KEY ({fk[3]}) REFERENCES {fk[2]}({fk[4]})")

    # Get indices (but not sqlite_autoindex)
    indices = conn.execute(sa.text(f"PRAGMA index_list({table_name})")).fetchall()
    idx_names = [i[1] for i in indices if not i[1].startswith('sqlite_')]

    new_table = f"{table_name}_new"
    col_str = ",\n".join(col_defs + fk_defs)
    conn.execute(sa.text(f"CREATE TABLE {new_table} ({col_str})"))
    conn.execute(sa.text(f"INSERT INTO {new_table} SELECT * FROM {table_name}"))
    conn.execute(sa.text(f"DROP TABLE {table_name}"))
    conn.execute(sa.text(f"ALTER TABLE {new_table} RENAME TO {table_name}"))

    # Recreate indices except the one for the altered column's old type
    for idx_name in idx_names:
        idx_info = conn.execute(sa.text(f"PRAGMA index_info({idx_name})")).fetchall()
        idx_cols = ", ".join(r[2] for r in idx_info)
        unique = any(i[2] for i in indices if i[1] == idx_name)
        conn.execute(sa.text(f"CREATE{' UNIQUE' if unique else ''} INDEX {idx_name} ON {table_name} ({idx_cols})"))

    # Set nullable if changed
    if nullable is not None:
        _set_nullable(table_name, col_name, nullable)


def _set_nullable(table_name: str, col_name: str, nullable: bool) -> None:
    """Change nullable setting via table rebuild (SQLite limitation)."""
    conn = op.get_bind()
    rows = conn.execute(sa.text(f"PRAGMA table_info({table_name})")).fetchall()
    col_info = {r[1]: r for r in rows}
    if col_name not in col_info:
        return
    new_val = 0 if nullable else 1
    orig = col_info[col_name]
    if (orig[3] == '0') == nullable:
        return  # Already correct

    col_defs = []
    fk_defs = []
    for r in rows:
        cname, ctype, notnull = r[1], r[2], r[3]
        cid = r[0]
        if cname == col_name:
            notnull = new_val
        col_defs.append(f"  {cname} {ctype}" + (" NOT NULL" if notnull else "") + (" PRIMARY KEY" if cid == orig[4] else ""))
    fks = conn.execute(sa.text(f"PRAGMA foreign_key_list({table_name})")).fetchall()
    for fk in fks:
        fk_defs.append(f"FOREIGN KEY ({fk[3]}) REFERENCES {fk[2]}({fk[4]})")

    new_table = f"{table_name}_new"
    col_str = ",\n".join(col_defs + fk_defs)
    conn.execute(sa.text(f"CREATE TABLE {new_table} ({col_str})"))
    conn.execute(sa.text(f"INSERT INTO {new_table} SELECT * FROM {table_name}"))
    conn.execute(sa.text(f"DROP TABLE {table_name}"))
    conn.execute(sa.text(f"ALTER TABLE {new_table} RENAME TO {table_name}"))
    # Recreate indices
    indices = conn.execute(sa.text(f"PRAGMA index_list({table_name})")).fetchall()
    idx_names = [i[1] for i in indices if not i[1].startswith('sqlite_')]
    for idx_name in idx_names:
        idx_info = conn.execute(sa.text(f"PRAGMA index_info({idx_name})")).fetchall()
        idx_cols = ", ".join(r[2] for r in idx_info)
        unique_idx = any(i[2] for i in indices if i[1] == idx_name)
        conn.execute(sa.text(f"CREATE{' UNIQUE' if unique_idx else ''} INDEX {idx_name} ON {table_name} ({idx_cols})"))


def upgrade() -> None:
    # ========================================================================
    # Musician v4: Create albums and music_releases tables (idempotent)
    # ========================================================================

    # --- Create music_releases table ---
    _safe_create_table_if_not_exists('music_releases', [
        SAFE_COL('id', sa.String(length=32), nullable=False),
        SAFE_COL('album_id', sa.String(length=32), nullable=True),
        SAFE_COL('work_variant_id', sa.String(length=32), nullable=True),
        SAFE_COL('title', sa.String(length=200), nullable=False),
        SAFE_COL('isrc', sa.String(length=12), nullable=True),
        SAFE_COL('audio_file_path', sa.String(length=500), nullable=True),
        SAFE_COL('duration_seconds', sa.Integer(), nullable=True),
        SAFE_COL('bitrate', sa.Integer(), nullable=True),
        SAFE_COL('format', sa.String(length=10), nullable=True),
        SAFE_COL('genre', sa.String(length=50), nullable=True),
        SAFE_COL('mood', sa.String(length=50), nullable=True),
        SAFE_COL('bpm', sa.Integer(), nullable=True),
        SAFE_COL('distribution_status', sa.String(length=20), nullable=True),
        SAFE_COL('created_at', sa.DateTime(), nullable=True),
        SAFE_COL('updated_at', sa.DateTime(), nullable=True),
    ], sa_fk=[
        sa.ForeignKeyConstraint(['album_id'], ['albums.id']),
        sa.ForeignKeyConstraint(['work_variant_id'], ['work_variants.id']),
    ], sa_pk=[sa.PrimaryKeyConstraint('id')])
    _safe_create_index('idx_release_isrc', 'music_releases', ['isrc'], unique=False)
    _safe_create_index('idx_release_album', 'music_releases', ['album_id'], unique=False)

    # --- Create / migrate albums table ---
    # Case A: albums table doesn't exist at all (brand-new DB)
    try:
        _safe_create_table_if_not_exists('albums', [
            SAFE_COL('id', sa.String(length=32), nullable=False),
            SAFE_COL('title', sa.String(length=200), nullable=False),
            SAFE_COL('album_type', sa.String(length=20), nullable=True),
            SAFE_COL('release_date', sa.DateTime(), nullable=True),
            SAFE_COL('cover_art_path', sa.String(length=500), nullable=True),
            SAFE_COL('label', sa.String(length=200), nullable=True),
            SAFE_COL('total_tracks', sa.Integer(), nullable=True),
            SAFE_COL('duration_seconds', sa.Integer(), nullable=True),
            SAFE_COL('created_at', sa.DateTime(), nullable=True),
            SAFE_COL('updated_at', sa.DateTime(), nullable=True),
        ], sa_pk=[sa.PrimaryKeyConstraint('id')])
        _safe_create_index('idx_album_type', 'albums', ['album_type'], unique=False)
    except Exception:
        pass

    # Case B: albums table already existed (from older schema) — transform it
    conn = op.get_bind()
    existing_tables = conn.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='albums'")
    ).fetchall()
    if existing_tables:
        # Check if the old schema had user_id column (indicates pre-transformation)
        alb_rows = conn.execute(sa.text("PRAGMA table_info(albums)")).fetchall()
        alb_cols = {r[1] for r in alb_rows} if alb_rows else set()
        if 'user_id' in alb_cols or 'is_active' in alb_cols:
            # Old schema transformation
            if 'cover_art_path' in alb_cols and 'cover_art_path' not in alb_cols - {'id', 'user_id', 'title', 'album_type', 'release_date', 'genre', 'isrc', 'cover_work_id', 'is_active', 'label', 'total_tracks', 'duration_seconds', 'created_at', 'updated_at'}:
                pass  # already has it
            elif 'cover_art_path' not in alb_cols:
                if _safe_add_column('albums', 'cover_art_path'):
                    op.add_column('albums', sa.Column('cover_art_path', sa.String(length=500), nullable=True))
            _alter_column_sqlite('albums', 'title', sa.String(length=200))
            _set_nullable('albums', 'album_type', nullable=True)
            _safe_drop_index('idx_album_user', 'albums')
            _safe_drop_column('albums', 'user_id')
            _safe_drop_column('albums', 'genre')
            _safe_drop_column('albums', 'cover_work_id')
            _safe_drop_column('albums', 'is_active')
            _safe_drop_column('albums', 'isrc')
            # Recreate album_type index after transformations
            _safe_create_index('idx_album_type', 'albums', ['album_type'], unique=False)

    # ========================================================================
    # Create split_sheets table (idempotent)
    # ========================================================================

    # --- Create split_sheets table ---
    _safe_create_table_if_not_exists('split_sheets', [
        SAFE_COL('id', sa.String(length=32), nullable=False),
        SAFE_COL('music_release_id', sa.String(length=32), nullable=False),
        SAFE_COL('title', sa.String(length=200), nullable=False),
        SAFE_COL('splits', sa.JSON(), nullable=True),
        SAFE_COL('publishing_share', sa.Float(), nullable=True),
        SAFE_COL('master_share', sa.Float(), nullable=True),
        SAFE_COL('status', sa.String(length=20), nullable=True),
        SAFE_COL('signed_at', sa.DateTime(), nullable=True),
        SAFE_COL('created_at', sa.DateTime(), nullable=True),
        SAFE_COL('updated_at', sa.DateTime(), nullable=True),
    ], sa_fk=[sa.ForeignKeyConstraint(['music_release_id'], ['music_releases.id'])], sa_pk=[sa.PrimaryKeyConstraint('id')])
    _safe_create_index('idx_split_status', 'split_sheets', ['status'], unique=False)

    # --- Foreign keys on campaigns, licenses ---
    # FK may already exist, suppress errors
    try:
        op.create_foreign_key(None, 'campaigns', 'design_listings', ['listing_id'], ['id'], ondelete='SET NULL')
    except Exception:
        pass
    _safe_create_index('idx_license_listing', 'licenses', ['listing_id'], unique=False)
    try:
        op.create_foreign_key(None, 'licenses', 'design_listings', ['listing_id'], ['id'], ondelete='SET NULL')
    except Exception:
        pass

    # --- monitor_results alterations ---
    if _safe_add_column('monitor_results', 'match_type'):
        op.add_column('monitor_results', sa.Column('match_type', sa.String(length=50), nullable=True))
    if _safe_add_column('monitor_results', 'confidence'):
        op.add_column('monitor_results', sa.Column('confidence', sa.Float(), nullable=True))
    _safe_create_index('idx_result_match_type', 'monitor_results', ['match_type'], unique=False)

    # --- orders alterations ---
    if _safe_add_column('orders', 'factory_id'):
        op.add_column('orders', sa.Column('factory_id', sa.String(length=32), nullable=True))
    if _safe_add_column('orders', 'sample_status'):
        op.add_column('orders', sa.Column('sample_status', sa.String(length=20), nullable=True))
    if _safe_add_column('orders', 'quality_inspection'):
        op.add_column('orders', sa.Column('quality_inspection', sa.String(length=20), nullable=True))
    if _safe_add_column('orders', 'production_quantity'):
        op.add_column('orders', sa.Column('production_quantity', sa.Integer(), nullable=True))
    if _safe_add_column('orders', 'delivery_date'):
        op.add_column('orders', sa.Column('delivery_date', sa.DateTime(), nullable=True))
    if _safe_add_column('orders', 'etasync_status'):
        op.add_column('orders', sa.Column('etasync_status', sa.String(length=20), nullable=True))
    _safe_create_index('idx_order_factory', 'orders', ['factory_id'], unique=False)
    try:
        op.create_foreign_key(None, 'orders', 'design_listings', ['listing_id'], ['id'], ondelete='SET NULL')
    except Exception:
        pass
    try:
        op.create_foreign_key(None, 'product_publishings', 'design_listings', ['listing_id'], ['id'], ondelete='CASCADE')
    except Exception:
        pass
    try:
        op.create_foreign_key(None, 'revenue_records', 'design_listings', ['listing_id'], ['id'], ondelete='SET NULL')
    except Exception:
        pass

    # --- idx_rfq_status (may already exist from partial migration) ---
    _safe_create_index('idx_rfq_status', 'rfqs', ['status'], unique=False)

    # --- work_variant_groups alterations ---
    if _safe_add_column('work_variant_groups', 'name'):
        op.add_column('work_variant_groups', sa.Column('name', sa.String(length=100), nullable=False))
    if _safe_add_column('work_variant_groups', 'description'):
        op.add_column('work_variant_groups', sa.Column('description', sa.String(length=500), nullable=True))
    if _safe_add_column('work_variant_groups', 'updated_at'):
        op.add_column('work_variant_groups', sa.Column('updated_at', sa.DateTime(), nullable=True))
    _safe_drop_index('idx_wvg_type', 'work_variant_groups')
    _safe_drop_column('work_variant_groups', 'thumbnail_path')
    _safe_drop_column('work_variant_groups', 'file_path')
    _safe_drop_column('work_variant_groups', 'variant_type')
    _safe_drop_column('work_variant_groups', 'height')
    _safe_drop_column('work_variant_groups', 'width')

    # --- works alterations ---
    if _safe_add_column('works', 'ai_tools_used'):
        op.add_column('works', sa.Column('ai_tools_used', sa.JSON(), nullable=True))
    if _safe_add_column('works', 'creator_type'):
        op.add_column('works', sa.Column('creator_type', sa.String(length=30), nullable=True))
    # completion_date: DATE -> String(20)
    _alter_column_sqlite('works', 'completion_date', sa.String(length=20))
    _set_nullable('works', 'completion_date', nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # SQLite cannot reverse ALTER COLUMN directly; use table rebuild
    _set_nullable('works', 'completion_date', nullable=False)
    _alter_column_sqlite('works', 'completion_date', sa.DATE())
    op.drop_column('works', 'creator_type')
    op.drop_column('works', 'ai_tools_used')
    op.add_column('work_variant_groups', sa.Column('width', sa.INTEGER(), nullable=True))
    op.add_column('work_variant_groups', sa.Column('height', sa.INTEGER(), nullable=True))
    op.add_column('work_variant_groups', sa.Column('variant_type', sa.String(length=20), nullable=False))
    op.add_column('work_variant_groups', sa.Column('file_path', sa.String(length=2000), nullable=True))
    op.add_column('work_variant_groups', sa.Column('thumbnail_path', sa.String(length=2000), nullable=True))
    op.create_index(op.f('idx_wvg_type'), 'work_variant_groups', ['variant_type'], unique=False)
    op.drop_column('work_variant_groups', 'updated_at')
    op.drop_column('work_variant_groups', 'description')
    op.drop_column('work_variant_groups', 'name')
    op.drop_constraint(None, 'revenue_records', type_='foreignkey')
    op.drop_constraint(None, 'product_publishings', type_='foreignkey')
    op.drop_constraint(None, 'orders', type_='foreignkey')
    op.drop_index('idx_order_factory', table_name='orders')
    op.drop_column('orders', 'etasync_status')
    op.drop_column('orders', 'delivery_date')
    op.drop_column('orders', 'production_quantity')
    op.drop_column('orders', 'quality_inspection')
    op.drop_column('orders', 'sample_status')
    op.drop_column('orders', 'factory_id')
    op.drop_index('idx_result_match_type', table_name='monitor_results')
    op.drop_column('monitor_results', 'confidence')
    op.drop_column('monitor_results', 'match_type')
    op.drop_constraint(None, 'licenses', type_='foreignkey')
    op.drop_index('idx_license_listing', table_name='licenses')
    op.drop_constraint(None, 'campaigns', type_='foreignkey')
    op.add_column('albums', sa.Column('isrc', sa.String(length=20), nullable=True))
    op.add_column('albums', sa.Column('is_active', sa.Boolean(), nullable=True))
    op.add_column('albums', sa.Column('cover_work_id', sa.String(length=32), nullable=True))
    op.add_column('albums', sa.Column('genre', sa.String(length=50), nullable=True))
    op.add_column('albums', sa.Column('user_id', sa.String(length=32), nullable=False))
    op.create_index(op.f('idx_album_user'), 'albums', ['user_id'], unique=False)
    _set_nullable('albums', 'album_type', nullable=False)
    _alter_column_sqlite('albums', 'title', sa.String(length=500))
    op.drop_column('albums', 'cover_art_path')
    op.drop_index('idx_split_status', table_name='split_sheets')
    op.drop_table('split_sheets')
    # ### end Alembic commands ###
