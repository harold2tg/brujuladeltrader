"""unified data ingestion - replace uploads with data sources

Revision ID: 008
Revises: 007
Create Date: 2025-06-09

This migration:
1. Creates the data_sources table (replaces uploads for broker integrations)
2. Migrates existing cTrader uploads to data_sources
3. Renames trades.upload_id → trades.data_source_id
4. Deletes file upload trades (can't be re-imported)
5. Drops the uploads table
6. Adds unique partial index for deal deduplication
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace uploads table with data_sources table."""

    # ========================================================================
    # Step 1: Create data_sources table
    # ========================================================================
    op.create_table(
        "data_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker", sa.String(50), nullable=False, comment="Broker identifier: ctrader, metatrader, binance, etc."),
        sa.Column("broker_account_id", sa.String(200), nullable=False, comment="Account ID from the broker"),
        sa.Column("name", sa.String(200), nullable=False, comment="Human-readable name"),
        sa.Column("sync_status", sa.String(20), nullable=False, server_default="idle", comment="idle | syncing | error"),
        sa.Column("last_synced_at", sa.TIMESTAMP(timezone=True), nullable=True, comment="Last successful sync"),
        sa.Column("trade_count", sa.Integer, nullable=False, server_default="0", comment="Total trades"),
        sa.Column("first_trade_at", sa.TIMESTAMP(timezone=True), nullable=True, comment="Earliest trade"),
        sa.Column("last_trade_at", sa.TIMESTAMP(timezone=True), nullable=True, comment="Most recent trade"),
        sa.Column("metadata", postgresql.JSON, nullable=False, server_default="{}", comment="Broker-specific data"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_user_broker_account",
        "data_sources",
        ["user_id", "broker", "broker_account_id"],
    )
    op.create_index("ix_data_sources_user_id", "data_sources", ["user_id"])

    # ========================================================================
    # Step 2: Migrate cTrader uploads → data_sources
    # ========================================================================
    op.execute("""
        INSERT INTO data_sources (
            id, user_id, broker, broker_account_id, name,
            sync_status, last_synced_at, trade_count,
            first_trade_at, last_trade_at,
            created_at, updated_at
        )
        SELECT
            u.id,
            u.user_id,
            'ctrader',
            COALESCE(u.period_label, 'unknown'),
            u.original_name,
            'idle',
            u.processed_at,
            COALESCE(u.total_trades, 0),
            u.date_from,
            u.date_to,
            u.created_at,
            COALESCE(u.processed_at, u.created_at)
        FROM uploads u
        WHERE u.source = 'ctrader'
    """)

    # ========================================================================
    # Step 3: Add data_source_id column to trades (nullable temporarily)
    # ========================================================================
    op.add_column(
        "trades",
        sa.Column("data_source_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # ========================================================================
    # Step 4: Copy upload_id → data_source_id for migrated trades
    # ========================================================================
    op.execute("""
        UPDATE trades
        SET data_source_id = upload_id
        WHERE upload_id IN (SELECT id FROM data_sources)
    """)

    # ========================================================================
    # Step 5: Delete trades linked to file uploads (orphaned)
    # ========================================================================
    op.execute("""
        DELETE FROM trades
        WHERE upload_id NOT IN (SELECT id FROM data_sources)
    """)

    # ========================================================================
    # Step 6: Make data_source_id NOT NULL
    # ========================================================================
    op.alter_column(
        "trades",
        "data_source_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

    # ========================================================================
    # Step 7: Drop old FK constraint and upload_id column
    # ========================================================================
    op.drop_constraint("trades_upload_id_fkey", "trades", type_="foreignkey")
    op.drop_index("ix_trades_upload_id", table_name="trades")
    op.drop_column("trades", "upload_id")

    # ========================================================================
    # Step 8: Add new FK constraint and index
    # ========================================================================
    op.create_foreign_key(
        "trades_data_source_id_fkey",
        "trades",
        "data_sources",
        ["data_source_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_trades_data_source_id", "trades", ["data_source_id"])

    # ========================================================================
    # Step 9: Add unique partial index for deal deduplication
    # ========================================================================
    op.create_index(
        "idx_trades_user_deal_id",
        "trades",
        ["user_id", "deal_id"],
        unique=True,
        postgresql_where=sa.text("deal_id IS NOT NULL"),
    )

    # ========================================================================
    # Step 10: Drop FK constraint and index from alert_history
    # (Must drop before dropping uploads table)
    # ========================================================================
    op.drop_constraint("alert_history_upload_id_fkey", "alert_history", type_="foreignkey")
    op.drop_index("ix_alert_history_upload_id", table_name="alert_history")

    # ========================================================================
    # Step 11: Drop uploads table
    # ========================================================================
    op.drop_table("uploads")


def downgrade() -> None:
    """Reverse the migration: recreate uploads from data_sources."""

    # ========================================================================
    # Step 11 reverse: Recreate uploads table
    # ========================================================================
    op.create_table(
        "uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("stored_name", sa.String(255), nullable=False),
        sa.Column("stored_path", sa.String(500), nullable=False),
        sa.Column("file_size_kb", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="file"),
        sa.Column("total_trades", sa.Integer, nullable=True),
        sa.Column("date_from", sa.Date, nullable=True),
        sa.Column("date_to", sa.Date, nullable=True),
        sa.Column("period_label", sa.String(50), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # ========================================================================
    # Step 10 reverse: Recreate FK constraint and index on alert_history
    # ========================================================================
    op.create_index("ix_alert_history_upload_id", "alert_history", ["upload_id"])
    op.create_foreign_key(
        "alert_history_upload_id_fkey",
        "alert_history",
        "uploads",
        ["upload_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ========================================================================
    # Step 9 reverse: Drop dedup index
    # ========================================================================
    op.drop_index("idx_trades_user_deal_id", table_name="trades")

    # ========================================================================
    # Step 8 reverse: Drop new FK and index
    # ========================================================================
    op.drop_index("ix_trades_data_source_id", table_name="trades")
    op.drop_constraint("trades_data_source_id_fkey", "trades", type_="foreignkey")

    # ========================================================================
    # Step 7 reverse: Add back upload_id column and FK
    # ========================================================================
    op.add_column(
        "trades",
        sa.Column("upload_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute("""
        UPDATE trades
        SET upload_id = data_source_id
    """)
    op.alter_column(
        "trades",
        "upload_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.create_foreign_key(
        "trades_upload_id_fkey",
        "trades",
        "uploads",
        ["upload_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_trades_upload_id", "trades", ["upload_id"])

    # ========================================================================
    # Step 6 reverse: Drop data_source_id column
    # ========================================================================
    op.drop_column("trades", "data_source_id")

    # ========================================================================
    # Step 2 reverse: Migrate data_sources → uploads
    # ========================================================================
    op.execute("""
        INSERT INTO uploads (
            id, user_id, original_name, stored_name, stored_path,
            file_size_kb, status, source, total_trades,
            date_from, date_to, period_label,
            created_at, processed_at
        )
        SELECT
            ds.id,
            ds.user_id,
            ds.name,
            CONCAT('ctrader_', ds.id::text, '.sync'),
            '',
            0,
            'ready',
            'ctrader',
            ds.trade_count,
            ds.first_trade_at,
            ds.last_trade_at,
            ds.broker_account_id,
            ds.created_at,
            ds.last_synced_at
        FROM data_sources ds
        WHERE ds.broker = 'ctrader'
    """)

    # ========================================================================
    # Step 1 reverse: Drop data_sources table
    # ========================================================================
    op.drop_index("ix_data_sources_user_id", table_name="data_sources")
    op.drop_table("data_sources")
