"""Add missing tables from models without prior migrations.

Revision ID: a1b2c3d4e5f7
Revises: 4023f131202d
Create Date: 2026-08-18
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f7'
down_revision = '4023f131202d'
branch_labels = None
depends_on = None


def upgrade():
    # ── Insurance ─────────────────────────────────────────────────────
    op.create_table('insurance_providers',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('name_zh', sa.String(length=200), nullable=False),
        sa.Column('name_en', sa.String(length=200), nullable=True),
        sa.Column('license_no', sa.String(length=100), nullable=True),
        sa.Column('api_base_url', sa.String(length=500), nullable=True),
        sa.Column('webhook_secret', sa.String(length=255), nullable=True),
        sa.Column('contact_email', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('insurance_products',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('product_key', sa.String(length=100), nullable=False),
        sa.Column('provider_id', sa.String(length=32), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('tier', sa.String(length=20), nullable=False),
        sa.Column('name_zh', sa.String(length=200), nullable=False),
        sa.Column('annual_min_yuan', sa.Float(), nullable=False),
        sa.Column('annual_max_yuan', sa.Float(), nullable=False),
        sa.Column('coverage_description', sa.Text(), nullable=True),
        sa.Column('max_coverage_yuan', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("tier IN ('basic', 'advanced', 'pro')", name='check_tier'),
        sa.ForeignKeyConstraint(['provider_id'], ['insurance_providers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_key', name='uq_product_key'),
    )
    op.create_index('ix_insurance_products_category', 'insurance_products', ['category'])
    op.create_index('ix_insurance_products_provider', 'insurance_products', ['provider_id'])

    op.create_table('insurance_policies',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('user_id', sa.String(length=32), nullable=False),
        sa.Column('product_id', sa.String(length=32), nullable=False),
        sa.Column('provider_id', sa.String(length=32), nullable=True),
        sa.Column('policy_number', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('annual_premium_yuan', sa.Float(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('external_policy_ref', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'active', 'expired', 'cancelled', 'claiming')",
            name='check_policy_status',
        ),
        sa.ForeignKeyConstraint(['product_id'], ['insurance_products.id']),
        sa.ForeignKeyConstraint(['provider_id'], ['insurance_providers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_insurance_policies_user_id', 'insurance_policies', ['user_id'])
    op.create_index('ix_insurance_policies_product_id', 'insurance_policies', ['product_id'])

    op.create_table('insurance_claims',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('policy_id', sa.String(length=32), nullable=False),
        sa.Column('claim_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('evidence_urls', sa.Text(), nullable=True),
        sa.Column('claimed_amount_yuan', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status IN ('submitted', 'under_review', 'approved', 'denied', 'paid')",
            name='check_claim_status',
        ),
        sa.CheckConstraint(
            "claim_type IN ('infringement', 'deepfake', 'theft', 'style_copy', 'other')",
            name='check_claim_type',
        ),
        sa.ForeignKeyConstraint(
            ['policy_id'], ['insurance_policies.id'], ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_insurance_claims_policy_id', 'insurance_claims', ['policy_id'])

    # ── Logistics ─────────────────────────────────────────────────────
    op.create_table('logistics_providers',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('contact_email', sa.String(length=100), nullable=True),
        sa.Column('contact_phone', sa.String(length=20), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('contract_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_logistics_status', 'logistics_providers', ['status'])
    op.create_index('idx_logistics_rating', 'logistics_providers', ['rating'])

    try:
        op.create_foreign_key(
            None, 'logistics_shipments', 'logistics_providers',
            ['provider_id'], ['id'], ondelete='SET NULL',
        )
    except Exception:
        pass

    # ── MCP (mcp_client.py) ──────────────────────────────────────────
    op.create_table('mcp_client_configs',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('endpoint_url', sa.String(length=500), nullable=False),
        sa.Column('protocol', sa.String(length=20), nullable=True),
        sa.Column('auth_type', sa.String(length=50), nullable=True),
        sa.Column('auth_token', sa.Text(), nullable=True),
        sa.Column('timeout_seconds', sa.Integer(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_connected_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_mcp_config_name'),
    )
    op.create_index('idx_mcp_config_name', 'mcp_client_configs', ['name'])
    op.create_index('idx_mcp_config_active', 'mcp_client_configs', ['is_active'])

    op.create_table('tool_events',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('config_id', sa.String(length=32), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('work_id', sa.String(length=32), nullable=True),
        sa.Column('user_id', sa.String(length=32), nullable=True),
        sa.Column('session_id', sa.String(length=32), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['config_id'], ['mcp_client_configs.id'], ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_tool_event_config', 'tool_events', ['config_id'])
    op.create_index('idx_tool_event_work', 'tool_events', ['work_id'])
    op.create_index('idx_tool_event_session', 'tool_events', ['session_id'])
    op.create_index('ix_tool_events_received_at', 'tool_events', ['received_at'])

    op.create_table('external_tool_connections',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('config_id', sa.String(length=32), nullable=False),
        sa.Column('connection_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('connected_at', sa.DateTime(), nullable=True),
        sa.Column('disconnected_at', sa.DateTime(), nullable=True),
        sa.Column('last_heartbeat_at', sa.DateTime(), nullable=True),
        sa.Column('event_count', sa.Integer(), nullable=True),
        sa.Column('conn_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['config_id'], ['mcp_client_configs.id'], ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_ext_conn_config', 'external_tool_connections', ['config_id'])
    op.create_index('idx_ext_conn_status', 'external_tool_connections', ['status'])


def downgrade():
    op.drop_table('external_tool_connections')
    op.drop_table('tool_events')
    op.drop_table('mcp_client_configs')
    op.drop_table('logistics_providers')
    op.drop_table('insurance_claims')
    op.drop_table('insurance_policies')
    op.drop_table('insurance_products')
    op.drop_table('insurance_providers')
