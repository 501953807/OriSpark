"""watermark_preset - Add watermark presets table.

Revision ID: watermark_v1
Revises: 
Create Date: 2026-07-28 21:00:00.000000

"""

from alembic import op
import sqlalchemy as src
from app.models.watermark_preset import PositionEnum

# revision identifiers, used by Alembic.
revision = 'wmk_preset_1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Apply migrations."""
    # Create watermark_presets table
    op.create_table('watermark_presets',
        src.Column('id', src.String(32), primary_key=True, default=lambda: ''),
        src.Column('name', src.String(100), nullable=False, index=True),
        src.Column('position', src.Enum(PositionEnum), nullable=False, default=PositionEnum.TOP_RIGHT),
        src.Column('opacity', src.Integer, nullable=False, default=100),
        src.Column('text', src.Text(), nullable=True),
        src.Column('image_path', src.Text(), nullable=True),
        src.Column('created_at', src.DateTime, default=src.sql.func.now()),
    )
    
    # Create indexes
    op.create_index('idx_wp_name', 'watermark_presets', ['name'])
    op.create_index('idx_wp_position', 'watermark_presets', ['position'])
    op.create_index('idx_wp_created', 'watermark_presets', ['created_at'])


def downgrade():
    """Revert migrations."""
    op.drop_index('idx_wp_created', table_name='watermark_presets')
    op.drop_index('idx_wp_position', table_name='watermark_presets')
    op.drop_index('idx_wp_name', table_name='watermark_presets')
    op.drop_table('watermark_presets')
