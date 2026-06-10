"""create trades table

Revision ID: 003
Revises: 002
Create Date: 2025-06-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create trades table."""
    op.create_table(
        "trades",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("upload_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("uploads.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("closed_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("entry_price", sa.Numeric(12, 5), nullable=False),
        sa.Column("close_price", sa.Numeric(12, 5), nullable=False),
        sa.Column("lot_size", sa.Numeric(8, 4), nullable=True),
        sa.Column("net_pnl", sa.Numeric(10, 2), nullable=False),
        sa.Column("balance", sa.Numeric(10, 2), nullable=True),
        sa.Column("hour_of_day", sa.SmallInteger, nullable=False),
        sa.Column("day_of_week", sa.SmallInteger, nullable=False),
        sa.Column("week_of_year", sa.SmallInteger, nullable=False),
        sa.Column("month", sa.SmallInteger, nullable=False),
        sa.Column("year", sa.SmallInteger, nullable=False),
        sa.Column("session", sa.String(20), nullable=False),
        sa.Column("is_winner", sa.Boolean, nullable=False),
        sa.Column("trade_number", sa.Integer, nullable=False),
        sa.Column("deal_id", sa.String(100), nullable=True),
    )
    op.create_index("ix_trades_upload_id", "trades", ["upload_id"])
    op.create_index("ix_trades_user_id", "trades", ["user_id"])


def downgrade() -> None:
    """Drop trades table."""
    op.drop_index("ix_trades_user_id")
    op.drop_index("ix_trades_upload_id")
    op.drop_table("trades")
