"""add logistics provider and shipment tables

Revision ID: f7e8d9c0b1a2
Revises: d62359dbdd00
Create Date: 2026-07-21 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7e8d9c0b1a2'
down_revision = 'd62359dbdd00'
branch_labels = None
depends_on = None


def upgrade():
    # === logistics_providers ===
    op.create_table(
        'logistics_providers',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('contact_email', sa.String(100), nullable=True),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('rating', sa.Float(), default=0.0),
        sa.Column('contract_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_index('idx_logistics_status', 'logistics_providers', ['status'])
    op.create_index('idx_logistics_rating', 'logistics_providers', ['rating'])

    # === logistics_shipments ===
    op.create_table(
        'logistics_shipments',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('contract_id', sa.String(32), sa.ForeignKey('contract_instances.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('provider_id', sa.String(32), sa.ForeignKey('logistics_providers.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('tracking_number', sa.String(100), nullable=True),
        sa.Column('carrier', sa.String(50), nullable=True),
        sa.Column('status', sa.String(30), default='pending'),
        sa.Column('shipped_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('estimated_delivery', sa.DateTime(), nullable=True),
        sa.Column('recipient_name', sa.String(100), nullable=True),
        sa.Column('recipient_address', sa.Text(), nullable=True),
        sa.Column('sender_name', sa.String(100), nullable=True),
        sa.Column('sender_address', sa.Text(), nullable=True),
        sa.Column('weight_kg', sa.Float(), nullable=True),
        sa.Column('dimensions_cm', sa.String(50), nullable=True),
        sa.Column('shipping_cost', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(10), default='CNY'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_index('idx_shipment_contract', 'logistics_shipments', ['contract_id'])
    op.create_index('idx_shipment_provider', 'logistics_shipments', ['provider_id'])
    op.create_index('idx_shipment_status', 'logistics_shipments', ['status'])
    op.create_index('idx_shipment_tracking', 'logistics_shipments', ['tracking_number'])

    # === logistics_tracking_events ===
    op.create_table(
        'logistics_tracking_events',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('shipment_id', sa.String(32), sa.ForeignKey('logistics_shipments.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_type', sa.String(30), nullable=False),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('occurred_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime()),
    )
    op.create_index('idx_tracking_event_shipment', 'logistics_tracking_events', ['shipment_id'])
    op.create_index('idx_tracking_event_time', 'logistics_tracking_events', ['occurred_at'])


def downgrade():
    op.drop_table('logistics_tracking_events')
    op.drop_table('logistics_shipments')
    op.drop_table('logistics_providers')
