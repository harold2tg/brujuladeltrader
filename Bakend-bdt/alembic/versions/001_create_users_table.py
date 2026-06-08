"""create users table

Revision ID: 001
Revises:
Create Date: 2025-06-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table."""
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("plan", sa.String(20), nullable=False, server_default="free"),
        sa.Column("language", sa.String(10), nullable=False, server_default="es"),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="America/Bogota"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    """Drop users table."""
    op.drop_table("users")
