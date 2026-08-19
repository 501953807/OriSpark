"""Schema drift fix v2: ensure missing columns exist

This migration is idempotent - it checks for column existence before adding.
All columns were previously added via ALTER TABLE, this just ensures proper migration tracking.

Revision ID: c80272753db2
Revises: a1b2c3d4e5f7
Create Date: 2026-08-19
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = 'c80272753db2'
down_revision: Union[str, None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_column_if_not_exists(table, column_name, column_def):
    """Add column only if it does not exist."""
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_cols = [c['name'] for c in inspector.get_columns(table)]
    if column_name not in existing_cols:
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(column_def)
        print(f"  Added column {table}.{column_name}")
    else:
        print(f"  Skipped (exists): {table}.{column_name}")


def _create_index_if_not_exists(table, index_name, columns):
    """Create index only if it does not exist."""
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_indexes = [i['name'] for i in inspector.get_indexes(table)]
    if index_name not in existing_indexes:
        op.create_index(index_name, table, columns)
        print(f"  Created index {index_name}")
    else:
        print(f"  Skipped index (exists): {index_name}")


def upgrade() -> None:
    # works table
    _add_column_if_not_exists('works', 'creator_id', sa.Column('creator_id', sa.String(length=32), nullable=True))
    _create_index_if_not_exists('works', 'idx_works_creator', ['creator_id'])
    _add_column_if_not_exists('works', 'work_operation_public', sa.Column('work_operation_public', sa.Boolean(), nullable=False, server_default='0'))
    _add_column_if_not_exists('works', 'operation_agreement_id', sa.Column('operation_agreement_id', sa.String(length=32), nullable=True))

    # users table
    _add_column_if_not_exists('users', 'bio', sa.Column('bio', sa.Text(), nullable=True))
    _add_column_if_not_exists('users', 'login_platform', sa.Column('login_platform', sa.String(length=20), nullable=True))
    _add_column_if_not_exists('users', 'participant_roles', sa.Column('participant_roles', sa.JSON(), nullable=True))
    _add_column_if_not_exists('users', 'is_platform_operator', sa.Column('is_platform_operator', sa.Boolean(), nullable=True, server_default='0'))
    _add_column_if_not_exists('users', 'is_payment_provider', sa.Column('is_payment_provider', sa.Boolean(), nullable=True, server_default='0'))
    _add_column_if_not_exists('users', 'is_insurer', sa.Column('is_insurer', sa.Boolean(), nullable=True, server_default='0'))
    _add_column_if_not_exists('users', 'is_logistics', sa.Column('is_logistics', sa.Boolean(), nullable=True, server_default='0'))
    _add_column_if_not_exists('users', 'company_name', sa.Column('company_name', sa.String(length=500), nullable=True))
    _add_column_if_not_exists('users', 'company_license_no', sa.Column('company_license_no', sa.String(length=200), nullable=True))
    _add_column_if_not_exists('users', 'company_address', sa.Column('company_address', sa.Text(), nullable=True))
    _add_column_if_not_exists('users', 'company_contact', sa.Column('company_contact', sa.String(length=200), nullable=True))
    _add_column_if_not_exists('users', 'company_phone', sa.Column('company_phone', sa.String(length=50), nullable=True))
    _add_column_if_not_exists('users', 'company_email', sa.Column('company_email', sa.String(length=200), nullable=True))
    _add_column_if_not_exists('users', 'qualification_verified', sa.Column('qualification_verified', sa.Boolean(), nullable=True, server_default='0'))
    _add_column_if_not_exists('users', 'qualification_verified_at', sa.Column('qualification_verified_at', sa.DateTime(), nullable=True))

    # ai_creation_sessions
    _add_column_if_not_exists('ai_creation_sessions', 'updated_at', sa.Column('updated_at', sa.DateTime(), nullable=True))

    # revenue_records
    _add_column_if_not_exists('revenue_records', 'income_category', sa.Column('income_category', sa.String(length=50), nullable=True))
    _add_column_if_not_exists('revenue_records', 'user_id', sa.Column('user_id', sa.String(length=32), nullable=True))
    _add_column_if_not_exists('revenue_records', 'source_description', sa.Column('source_description', sa.Text(), nullable=True))
    _add_column_if_not_exists('revenue_records', 'recorded_date', sa.Column('recorded_date', sa.DateTime(), nullable=True))
    _add_column_if_not_exists('revenue_records', 'is_verified', sa.Column('is_verified', sa.Boolean(), nullable=True))
    _add_column_if_not_exists('revenue_records', 'extra_metadata', sa.Column('extra_metadata', sa.JSON(), nullable=True))
    _create_index_if_not_exists('revenue_records', 'ix_revenue_records_user_id', ['user_id'])

    # rfqs
    _create_index_if_not_exists('rfqs', 'idx_rfqs_status', ['status'])

    # video_fingerprint_config
    _add_column_if_not_exists('video_fingerprint_config', 'name', sa.Column('name', sa.String(length=100), nullable=False, server_default='default'))
    _add_column_if_not_exists('video_fingerprint_config', 'algorithm', sa.Column('algorithm', sa.String(length=20), nullable=True))
    _add_column_if_not_exists('video_fingerprint_config', 'threshold', sa.Column('threshold', sa.Float(), nullable=True))
    _add_column_if_not_exists('video_fingerprint_config', 'is_active', sa.Column('is_active', sa.Integer(), nullable=True))
    _add_column_if_not_exists('video_fingerprint_config', 'settings', sa.Column('settings', sa.JSON(), nullable=True))
    _add_column_if_not_exists('video_fingerprint_config', 'updated_at', sa.Column('updated_at', sa.DateTime(), nullable=True))

    # video_frame_fingerprints
    _add_column_if_not_exists('video_frame_fingerprints', 'work_id', sa.Column('work_id', sa.String(length=32), nullable=True))
    _add_column_if_not_exists('video_frame_fingerprints', 'config_id', sa.Column('config_id', sa.String(length=32), nullable=True))
    _add_column_if_not_exists('video_frame_fingerprints', 'frame_hash', sa.Column('frame_hash', sa.String(length=64), nullable=True))
    _add_column_if_not_exists('video_frame_fingerprints', 'timestamp_ms', sa.Column('timestamp_ms', sa.Float(), nullable=True))
    _add_column_if_not_exists('video_frame_fingerprints', 'similarity_score', sa.Column('similarity_score', sa.Float(), nullable=True))
    _add_column_if_not_exists('video_frame_fingerprints', 'matched_work_id', sa.Column('matched_work_id', sa.String(length=32), nullable=True))
    _add_column_if_not_exists('video_frame_fingerprints', 'updated_at', sa.Column('updated_at', sa.DateTime(), nullable=True))
    _create_index_if_not_exists('video_frame_fingerprints', 'idx_vff_config', ['config_id'])
    _create_index_if_not_exists('video_frame_fingerprints', 'idx_vff_work', ['work_id', 'frame_number'])

    # watermark_presets
    _add_column_if_not_exists('watermark_presets', 'position', sa.Column('position', sa.String(length=50), nullable=True))
    _add_column_if_not_exists('watermark_presets', 'opacity', sa.Column('opacity', sa.Float(), nullable=True))
    _add_column_if_not_exists('watermark_presets', 'text', sa.Column('text', sa.Text(), nullable=True))
    _add_column_if_not_exists('watermark_presets', 'image_path', sa.Column('image_path', sa.String(length=2000), nullable=True))
    _add_column_if_not_exists('watermark_presets', 'updated_at', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Conservative: no downgrades, data may be lost
    pass
