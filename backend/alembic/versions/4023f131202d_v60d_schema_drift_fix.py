"""v60d_schema_drift_fix

Revision ID: 4023f131202d
Revises: v60c_add_work_operation_public
Create Date: 2026-08-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '4023f131202d'
down_revision: Union[str, None] = 'v60c_add_work_operation_public'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Helper for SQLite-safe schema operations
sqlite = True


def _drop_table_if_exists(table_name):
    """Drop table if it exists."""
    op.execute(f"DROP TABLE IF EXISTS [{table_name}]")


def _drop_index_if_exists(table_name, index_name):
    """Drop index if it exists."""
    op.execute(f"DROP INDEX IF EXISTS [{index_name}]")


def upgrade() -> None:
    # --- Drop removed tables and their indexes ---
    _drop_index_if_exists('external_tool_connections', 'idx_ext_conn_config')
    _drop_index_if_exists('external_tool_connections', 'idx_ext_conn_status')
    _drop_table_if_exists('external_tool_connections')

    _drop_index_if_exists('mcp_client_configs', 'idx_mcp_config_active')
    _drop_index_if_exists('mcp_client_configs', 'idx_mcp_config_name')
    _drop_table_if_exists('mcp_client_configs')

    # tool_events and mcp_client_configs don't exist in DB yet, skip

    # --- ai_creation_sessions: make prompt nullable, ensure updated_at ---
    # Column already exists but is NOT NULL; SQLite can't ALTER column constraint
    # so we recreate the table (0 rows of data)
    _drop_index_if_exists('ai_creation_sessions', 'idx_ai_session_work')
    op.execute("""
        CREATE TABLE ai_creation_sessions_new (
            id VARCHAR(32) NOT NULL,
            work_id VARCHAR(32) NOT NULL,
            tool_name VARCHAR(100) NOT NULL,
            tool_version VARCHAR(50),
            prompt TEXT,
            prompt_history JSON,
            seed INTEGER,
            parameters JSON,
            negative_prompt TEXT,
            model_name VARCHAR(500),
            lora_names JSON,
            output_images JSON,
            human_interventions JSON,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(work_id) REFERENCES works(id) ON DELETE CASCADE
        )
    """)
    op.execute("INSERT INTO ai_creation_sessions_new SELECT * FROM ai_creation_sessions")
    _drop_table_if_exists('ai_creation_sessions')
    op.execute("ALTER TABLE ai_creation_sessions_new RENAME TO ai_creation_sessions")
    op.create_index('idx_ai_session_work', 'ai_creation_sessions', ['work_id'])

    # --- etsy_orders: make listing_id nullable ---
    # SQLite can't alter column constraint; recreate (small data)
    op.execute("""
        CREATE TABLE etsy_orders_new (
            id VARCHAR(32) NOT NULL,
            user_id VARCHAR(32) NOT NULL,
            listing_id VARCHAR(32),
            etsy_order_id VARCHAR(100) NOT NULL,
            buyer_name VARCHAR(200),
            buyer_country VARCHAR(100),
            order_total FLOAT NOT NULL,
            shipping_cost FLOAT,
            tax FLOAT,
            order_date DATETIME NOT NULL,
            shipping_deadline DATETIME,
            status VARCHAR(20),
            tracking_number VARCHAR(100),
            notes TEXT,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(listing_id) REFERENCES etsy_listings(id),
            UNIQUE (etsy_order_id)
        )
    """)
    op.execute("INSERT INTO etsy_orders_new SELECT * FROM etsy_orders")
    _drop_table_if_exists('etsy_orders')
    op.execute("ALTER TABLE etsy_orders_new RENAME TO etsy_orders")
    op.create_index('idx_etsy_order_etsy', 'etsy_orders', ['etsy_order_id'])
    op.create_index('idx_etsy_order_status', 'etsy_orders', ['status'])
    op.create_index('idx_etsy_order_user', 'etsy_orders', ['user_id'])

    # --- revenue_records: add new columns, make platform nullable ---
    # Add new columns (SQLite supports ADD COLUMN)
    op.add_column('revenue_records', sa.Column('income_category', sa.String(50), nullable=True))
    op.add_column('revenue_records', sa.Column('user_id', sa.String(32), nullable=True))
    op.add_column('revenue_records', sa.Column('source_description', sa.Text(), nullable=True))
    op.add_column('revenue_records', sa.Column('recorded_date', sa.DateTime(), nullable=True))
    op.add_column('revenue_records', sa.Column('is_verified', sa.Boolean(), default=False, nullable=True))
    op.add_column('revenue_records', sa.Column('extra_metadata', sa.JSON(), nullable=True))
    # Make platform nullable via recreate
    op.execute("""
        CREATE TABLE revenue_records_new (
            id VARCHAR(32) NOT NULL,
            product_id VARCHAR(32),
            listing_id VARCHAR(32),
            platform VARCHAR(50),
            amount FLOAT NOT NULL,
            currency VARCHAR(10),
            date DATE,
            order_count INTEGER,
            source VARCHAR(50),
            refund_amount FLOAT,
            platform_fee FLOAT,
            net_revenue FLOAT,
            income_category VARCHAR(50),
            user_id VARCHAR(32),
            source_description TEXT,
            recorded_date DATETIME,
            is_verified BOOLEAN,
            extra_metadata JSON,
            notes TEXT,
            created_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL,
            FOREIGN KEY(listing_id) REFERENCES design_listings(id) ON DELETE SET NULL
        )
    """)
    op.execute("""
        INSERT INTO revenue_records_new
        SELECT id, product_id, listing_id, NULL, amount, currency, date, order_count,
               source, refund_amount, platform_fee, net_revenue,
               NULL, NULL, NULL, NULL, NULL, NULL, notes, created_at
        FROM revenue_records
    """)
    _drop_table_if_exists('revenue_records')
    op.execute("ALTER TABLE revenue_records_new RENAME TO revenue_records")
    op.create_index('idx_revenue_date', 'revenue_records', ['date'])
    op.create_index('idx_revenue_platform', 'revenue_records', ['platform'])
    op.create_index('ix_revenue_records_user_id', 'revenue_records', ['user_id'])

    # --- rfqs: add status index ---
    op.create_index('idx_rfqs_status', 'rfqs', ['status'])

    # --- video_fingerprint_config: rename columns, add new ones ---
    # SQLite can't rename columns or drop columns directly
    # Recreate table (0 rows of data)
    op.execute("""
        CREATE TABLE video_fingerprint_config_new (
            id VARCHAR(32) NOT NULL,
            name VARCHAR(100) NOT NULL,
            algorithm VARCHAR(20),
            frame_interval INTEGER,
            threshold FLOAT,
            is_active INTEGER,
            settings JSON,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id)
        )
    """)
    op.execute("""
        INSERT INTO video_fingerprint_config_new
        SELECT id, config_name, hash_algorithm, frame_interval,
               0.85, COALESCE(enabled, 1), '{}', created_at, CURRENT_TIMESTAMP
        FROM video_fingerprint_config
    """)
    _drop_table_if_exists('video_fingerprint_config')
    op.execute("ALTER TABLE video_fingerprint_config_new RENAME TO video_fingerprint_config")

    # --- video_frame_fingerprints: major refactor ---
    # SQLite can't drop/add columns and change FKs easily
    # Recreate table (0 rows of data)
    op.execute("""
        CREATE TABLE video_frame_fingerprints_new (
            id VARCHAR(32) NOT NULL,
            work_id VARCHAR(32) NOT NULL,
            config_id VARCHAR(32),
            frame_number INTEGER NOT NULL,
            frame_hash VARCHAR(64) NOT NULL,
            timestamp_ms FLOAT,
            similarity_score FLOAT,
            matched_work_id VARCHAR(32),
            hash_type VARCHAR(20),
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(work_id) REFERENCES works(id) ON DELETE CASCADE,
            FOREIGN KEY(config_id) REFERENCES video_fingerprint_config(id) ON DELETE SET NULL
        )
    """)
    op.execute("""
        INSERT INTO video_frame_fingerprints_new
        SELECT id, video_work_id, NULL, frame_number, perceptual_hash,
               timestamp * 1000, NULL, NULL, hash_type, created_at, CURRENT_TIMESTAMP
        FROM video_frame_fingerprints
    """)
    _drop_table_if_exists('video_frame_fingerprints')
    op.execute("ALTER TABLE video_frame_fingerprints_new RENAME TO video_frame_fingerprints")
    op.create_index('idx_vff_work', 'video_frame_fingerprints', ['work_id', 'frame_number'])
    op.create_index('idx_vff_hash', 'video_frame_fingerprints', ['frame_hash'])
    op.create_index('idx_vff_config', 'video_frame_fingerprints', ['config_id'])

    # --- watermark_presets: full schema migration ---
    # Has 3 rows of data; migrate carefully
    # Current columns: id, name, description, watermark_type, config, is_default,
    #   created_by, created_at, updated_at, position_old, opacity, text, image_path, position
    # Target columns: id, name, position(Enum), opacity, text, image_path, created_at
    _drop_index_if_exists('watermark_presets', 'idx_wp_type')
    _drop_index_if_exists('watermark_presets', 'idx_wp_user')
    _drop_index_if_exists('watermark_presets', 'idx_wp_created')
    _drop_index_if_exists('watermark_presets', 'idx_wp_position')

    op.execute("""
        CREATE TABLE watermark_presets_new (
            id VARCHAR(32) NOT NULL,
            name VARCHAR(100) NOT NULL,
            position VARCHAR(20) NOT NULL DEFAULT 'top-right',
            opacity INTEGER NOT NULL DEFAULT 100,
            text TEXT,
            image_path TEXT,
            created_at DATETIME,
            PRIMARY KEY (id)
        )
    """)
    op.execute("""
        INSERT INTO watermark_presets_new
        SELECT id, name,
               CASE WHEN position IN ('top-left','top-right','bottom-left','bottom-right')
                    THEN position ELSE 'top-right' END,
               COALESCE(opacity, 100), text, image_path, created_at
        FROM watermark_presets
    """)
    _drop_table_if_exists('watermark_presets')
    op.execute("ALTER TABLE watermark_presets_new RENAME TO watermark_presets")
    op.create_index('idx_wp_name', 'watermark_presets', ['name'])
    op.create_index('idx_wp_position', 'watermark_presets', ['position'])
    op.create_index('idx_wp_created', 'watermark_presets', ['created_at'])

    # --- works: ensure creator_id FK ---
    # creator_id and work_operation_public already exist in DB
    # Add explicit FK if missing (SQLite doesn't support ADD CONSTRAINT)
    # Just create the index
    op.create_index('ix_works_creator_id', 'works', ['creator_id'])


def downgrade() -> None:
    # Reverse operations — best-effort for SQLite

    # --- works ---
    _drop_index_if_exists('works', 'ix_works_creator_id')

    # --- watermark_presets: restore old schema ---
    _drop_index_if_exists('watermark_presets', 'idx_wp_name')
    _drop_index_if_exists('watermark_presets', 'idx_wp_position')
    _drop_index_if_exists('watermark_presets', 'idx_wp_created')

    op.execute("""
        CREATE TABLE watermark_presets_new (
            id VARCHAR(32) NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            watermark_type VARCHAR(20) NOT NULL,
            config JSON NOT NULL,
            is_default BOOLEAN,
            created_by VARCHAR(32),
            created_at DATETIME,
            updated_at DATETIME,
            position_old VARCHAR(20) NOT NULL DEFAULT 'top-right',
            opacity INTEGER NOT NULL DEFAULT 100,
            text TEXT,
            image_path TEXT,
            position VARCHAR(20) NOT NULL DEFAULT 'top-right',
            PRIMARY KEY (id),
            FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    op.execute("""
        INSERT INTO watermark_presets_new
        SELECT id, name, NULL, 'text', '{}', NULL, NULL, created_at, NULL,
               'top-right', opacity, text, image_path, position
        FROM watermark_presets
    """)
    _drop_table_if_exists('watermark_presets')
    op.execute("ALTER TABLE watermark_presets_new RENAME TO watermark_presets")
    op.create_index('idx_wp_type', 'watermark_presets', ['watermark_type'])
    op.create_index('idx_wp_user', 'watermark_presets', ['created_by'])
    op.create_index('idx_wp_created', 'watermark_presets', ['created_at'])
    op.create_index('idx_wp_position', 'watermark_presets', ['position'])

    # --- video_frame_fingerprints: restore ---
    _drop_index_if_exists('video_frame_fingerprints', 'idx_vff_work')
    _drop_index_if_exists('video_frame_fingerprints', 'idx_vff_hash')
    _drop_index_if_exists('video_frame_fingerprints', 'idx_vff_config')

    op.execute("""
        CREATE TABLE video_frame_fingerprints_new (
            id VARCHAR(32) NOT NULL,
            video_work_id VARCHAR(32) NOT NULL,
            frame_number INTEGER NOT NULL,
            timestamp FLOAT,
            perceptual_hash VARCHAR(64) NOT NULL,
            hash_type VARCHAR(20),
            created_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(video_work_id) REFERENCES works(id) ON DELETE CASCADE
        )
    """)
    op.execute("""
        INSERT INTO video_frame_fingerprints_new
        SELECT id, work_id, frame_number, COALESCE(timestamp_ms / 1000.0, 0),
               frame_hash, hash_type, created_at
        FROM video_frame_fingerprints
    """)
    _drop_table_if_exists('video_frame_fingerprints')
    op.execute("ALTER TABLE video_frame_fingerprints_new RENAME TO video_frame_fingerprints")
    op.create_index('idx_vff_video', 'video_frame_fingerprints', ['video_work_id', 'frame_number'])
    op.create_index('idx_vff_hash', 'video_frame_fingerprints', ['perceptual_hash'])

    # --- video_fingerprint_config: restore ---
    op.execute("""
        CREATE TABLE video_fingerprint_config_new (
            id VARCHAR(32) NOT NULL,
            config_name VARCHAR(100) NOT NULL,
            frame_interval INTEGER,
            hash_algorithm VARCHAR(20),
            enabled INTEGER,
            created_at DATETIME,
            PRIMARY KEY (id)
        )
    """)
    op.execute("""
        INSERT INTO video_fingerprint_config_new
        SELECT id, name, frame_interval, algorithm, is_active, created_at
        FROM video_fingerprint_config
    """)
    _drop_table_if_exists('video_fingerprint_config')
    op.execute("ALTER TABLE video_fingerprint_config_new RENAME TO video_fingerprint_config")

    # --- rfqs: drop status index ---
    _drop_index_if_exists('rfqs', 'idx_rfqs_status')

    # --- revenue_records: restore ---
    _drop_index_if_exists('revenue_records', 'ix_revenue_records_user_id')
    op.execute("""
        CREATE TABLE revenue_records_new (
            id VARCHAR(32) NOT NULL,
            product_id VARCHAR(32),
            listing_id VARCHAR(32),
            platform VARCHAR(50) NOT NULL,
            amount FLOAT NOT NULL,
            currency VARCHAR(10),
            date DATE,
            order_count INTEGER,
            source VARCHAR(50),
            refund_amount FLOAT,
            platform_fee FLOAT,
            net_revenue FLOAT,
            notes TEXT,
            created_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL,
            FOREIGN KEY(listing_id) REFERENCES design_listings(id) ON DELETE SET NULL
        )
    """)
    op.execute("""
        INSERT INTO revenue_records_new
        SELECT id, product_id, listing_id, COALESCE(platform, 'manual'), amount,
               currency, date, order_count, source, refund_amount, platform_fee,
               net_revenue, notes, created_at
        FROM revenue_records
    """)
    _drop_table_if_exists('revenue_records')
    op.execute("ALTER TABLE revenue_records_new RENAME TO revenue_records")
    op.create_index('idx_revenue_date', 'revenue_records', ['date'])
    op.create_index('idx_revenue_platform', 'revenue_records', ['platform'])

    # --- etsy_orders: restore listing_id NOT NULL ---
    op.execute("""
        CREATE TABLE etsy_orders_new (
            id VARCHAR(32) NOT NULL,
            user_id VARCHAR(32) NOT NULL,
            listing_id VARCHAR(32) NOT NULL,
            etsy_order_id VARCHAR(100) NOT NULL,
            buyer_name VARCHAR(200),
            buyer_country VARCHAR(100),
            order_total FLOAT NOT NULL,
            shipping_cost FLOAT,
            tax FLOAT,
            order_date DATETIME NOT NULL,
            shipping_deadline DATETIME,
            status VARCHAR(20),
            tracking_number VARCHAR(100),
            notes TEXT,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(listing_id) REFERENCES etsy_listings(id),
            UNIQUE (etsy_order_id)
        )
    """)
    op.execute("INSERT INTO etsy_orders_new SELECT * FROM etsy_orders")
    _drop_table_if_exists('etsy_orders')
    op.execute("ALTER TABLE etsy_orders_new RENAME TO etsy_orders")
    op.create_index('idx_etsy_order_etsy', 'etsy_orders', ['etsy_order_id'])
    op.create_index('idx_etsy_order_status', 'etsy_orders', ['status'])
    op.create_index('idx_etsy_order_user', 'etsy_orders', ['user_id'])

    # --- ai_creation_sessions: restore prompt NOT NULL ---
    _drop_index_if_exists('ai_creation_sessions', 'idx_ai_session_work')
    op.execute("""
        CREATE TABLE ai_creation_sessions_new (
            id VARCHAR(32) NOT NULL,
            work_id VARCHAR(32) NOT NULL,
            tool_name VARCHAR(100) NOT NULL,
            tool_version VARCHAR(50),
            prompt TEXT NOT NULL,
            prompt_history JSON,
            seed INTEGER,
            parameters JSON,
            negative_prompt TEXT,
            model_name VARCHAR(500),
            lora_names JSON,
            output_images JSON,
            human_interventions JSON,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(work_id) REFERENCES works(id) ON DELETE CASCADE
        )
    """)
    op.execute("INSERT INTO ai_creation_sessions_new SELECT * FROM ai_creation_sessions")
    _drop_table_if_exists('ai_creation_sessions')
    op.execute("ALTER TABLE ai_creation_sessions_new RENAME TO ai_creation_sessions")
    op.create_index('idx_ai_session_work', 'ai_creation_sessions', ['work_id'])

    # --- Recreate dropped tables (empty) ---
    op.execute("""
        CREATE TABLE mcp_client_configs (
            id VARCHAR(32) NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            endpoint_url VARCHAR(500) NOT NULL,
            protocol VARCHAR(20),
            auth_type VARCHAR(50),
            auth_token TEXT,
            timeout_seconds INTEGER,
            retry_count INTEGER,
            is_active BOOLEAN,
            last_connected_at DATETIME,
            last_error TEXT,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            UNIQUE (name)
        )
    """)
    op.create_index('idx_mcp_config_name', 'mcp_client_configs', ['name'])
    op.create_index('idx_mcp_config_active', 'mcp_client_configs', ['is_active'])

    op.execute("""
        CREATE TABLE external_tool_connections (
            id VARCHAR(32) NOT NULL,
            config_id VARCHAR(32) NOT NULL,
            connection_id VARCHAR(100) NOT NULL,
            status VARCHAR(20),
            connected_at DATETIME,
            disconnected_at DATETIME,
            last_heartbeat_at DATETIME,
            event_count INTEGER,
            conn_metadata JSON,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(config_id) REFERENCES mcp_client_configs(id) ON DELETE CASCADE
        )
    """)
    op.create_index('idx_ext_conn_status', 'external_tool_connections', ['status'])
    op.create_index('idx_ext_conn_config', 'external_tool_connections', ['config_id'])

    op.execute("""
        CREATE TABLE tool_events (
            id VARCHAR(32) NOT NULL,
            config_id VARCHAR(32) NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            event_data JSON,
            work_id VARCHAR(32),
            user_id VARCHAR(32),
            session_id VARCHAR(32),
            received_at DATETIME,
            processed BOOLEAN,
            processed_at DATETIME,
            error_message TEXT,
            created_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(config_id) REFERENCES mcp_client_configs(id) ON DELETE CASCADE
        )
    """)
    op.create_index('ix_tool_events_received_at', 'tool_events', ['received_at'])
    op.create_index('idx_tool_event_work', 'tool_events', ['work_id'])
    op.create_index('idx_tool_event_session', 'tool_events', ['session_id'])
    op.create_index('idx_tool_event_config', 'tool_events', ['config_id'])
