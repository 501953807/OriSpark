"""add photographer fields to work_variants

Revision ID: 5e2337c33efd
Revises: 9afc1bee1782
Create Date: 2026-06-30 23:43:21.733406
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '5e2337c33efd'
down_revision: Union[str, None] = '9afc1bee1782'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('work_variants', sa.Column('camera_model', sa.String(length=100), nullable=True))
    op.add_column('work_variants', sa.Column('lens', sa.String(length=200), nullable=True))
    op.add_column('work_variants', sa.Column('iso', sa.Integer(), nullable=True))
    op.add_column('work_variants', sa.Column('aperture', sa.String(length=20), nullable=True))
    op.add_column('work_variants', sa.Column('shutter_speed', sa.String(length=30), nullable=True))
    op.add_column('work_variants', sa.Column('focal_length', sa.String(length=30), nullable=True))
    op.add_column('work_variants', sa.Column('gps_latitude', sa.Float(), nullable=True))
    op.add_column('work_variants', sa.Column('gps_longitude', sa.Float(), nullable=True))
    op.add_column('work_variants', sa.Column('gps_altitude', sa.Float(), nullable=True))
    op.add_column('work_variants', sa.Column('raw_file_path', sa.String(length=500), nullable=True))
    op.add_column('work_variants', sa.Column('shot_status', sa.String(length=20), nullable=True, server_default='unreviewed'))
    op.add_column('work_variants', sa.Column('shot_notes', sa.Text(), nullable=True))
    op.add_column('work_variants', sa.Column('stock_channels', sa.JSON(), nullable=True))
    op.create_index('idx_wv_camera', 'work_variants', ['camera_model'], unique=False)
    op.create_index('idx_wv_raw_path', 'work_variants', ['raw_file_path'], unique=False)
    op.create_index('idx_wv_shot_status', 'work_variants', ['shot_status'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_wv_shot_status', table_name='work_variants')
    op.drop_index('idx_wv_raw_path', table_name='work_variants')
    op.drop_index('idx_wv_camera', table_name='work_variants')
    op.drop_column('work_variants', 'stock_channels')
    op.drop_column('work_variants', 'shot_notes')
    op.drop_column('work_variants', 'shot_status')
    op.drop_column('work_variants', 'raw_file_path')
    op.drop_column('work_variants', 'gps_altitude')
    op.drop_column('work_variants', 'gps_longitude')
    op.drop_column('work_variants', 'gps_latitude')
    op.drop_column('work_variants', 'focal_length')
    op.drop_column('work_variants', 'shutter_speed')
    op.drop_column('work_variants', 'aperture')
    op.drop_column('work_variants', 'iso')
    op.drop_column('work_variants', 'lens')
    op.drop_column('work_variants', 'camera_model')
