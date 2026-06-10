"""create ctrader_credentials table

Revision ID: 004
Revises: 003
Create Date: 2025-06-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ctrader_credentials table."""
    op.create_table(
        "ctrader_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_id_enc", sa.Text, nullable=False),
        sa.Column("client_secret_enc", sa.Text, nullable=False),
        sa.Column("access_token_enc", sa.Text, nullable=False),
        sa.Column("account_id_enc", sa.Text, nullable=False),
        sa.Column("account_name", sa.String(100), nullable=True),
        sa.Column("broker_name", sa.String(100), nullable=True),
        sa.Column("is_demo", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop ctrader_credentials table."""
    op.drop_table("ctrader_credentials")
