"""add unique constraint to ai_credentials

Revision ID: 007
Revises: 006
Create Date: 2025-06-09
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers
revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint on (user_id, provider) for ai_credentials."""
    op.create_unique_constraint(
        "uq_ai_credentials_user_provider",
        "ai_credentials",
        ["user_id", "provider"],
    )


def downgrade() -> None:
    """Drop unique constraint from ai_credentials."""
    op.drop_constraint("uq_ai_credentials_user_provider", "ai_credentials", type_="unique")
