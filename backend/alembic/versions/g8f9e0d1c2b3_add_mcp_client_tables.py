"""add MCP client tables

Revision ID: g8f9e0d1c2b3
Revises: f7e8d9c0b1a2
Create Date: 2026-07-21 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g8f9e0d1c2b3'
down_revision = 'f07708b3b832'
branch_labels = None
depends_on = None


def upgrade():
    # === mcp_client_configs ===
    op.create_table(
        'mcp_client_configs',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('endpoint_url', sa.String(500), nullable=False),
        sa.Column('protocol', sa.String(20), default='http'),
        sa.Column('auth_type', sa.String(50), default='none'),
        sa.Column('auth_token', sa.Text(), nullable=True),
        sa.Column('timeout_seconds', sa.Integer(), default=30),
        sa.Column('retry_count', sa.Integer(), default=3),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_connected_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_index('idx_mcp_config_name', 'mcp_client_configs', ['name'])
    op.create_index('idx_mcp_config_active', 'mcp_client_configs', ['is_active'])

    # === tool_events ===
    op.create_table(
        'tool_events',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('config_id', sa.String(32), sa.ForeignKey('mcp_client_configs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('work_id', sa.String(32), nullable=True, index=True),
        sa.Column('user_id', sa.String(32), nullable=True),
        sa.Column('session_id', sa.String(32), nullable=True, index=True),
        sa.Column('received_at', sa.DateTime(), index=True),
        sa.Column('processed', sa.Boolean(), default=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime()),
    )

    # === external_tool_connections ===
    op.create_table(
        'external_tool_connections',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('config_id', sa.String(32), sa.ForeignKey('mcp_client_configs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('connection_id', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), default='disconnected'),
        sa.Column('connected_at', sa.DateTime(), nullable=True),
        sa.Column('disconnected_at', sa.DateTime(), nullable=True),
        sa.Column('last_heartbeat_at', sa.DateTime(), nullable=True),
        sa.Column('event_count', sa.Integer(), default=0),
        sa.Column('conn_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_index('idx_ext_conn_status', 'external_tool_connections', ['status'])


def downgrade():
    op.drop_table('external_tool_connections')
    op.drop_table('tool_events')
    op.drop_table('mcp_client_configs')
