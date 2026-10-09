"""add refresh_token_enc to ctrader_credentials

Revision ID: 010
Revises: 009
Create Date: 2025-10-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ctrader_credentials",
        sa.Column("refresh_token_enc", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ctrader_credentials", "refresh_token_enc")
