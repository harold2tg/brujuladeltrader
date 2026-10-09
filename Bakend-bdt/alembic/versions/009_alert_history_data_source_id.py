"""alert_history: rename upload_id to data_source_id, update FK

Revision ID: 009
Revises: 008
Create Date: 2025-06-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename alert_history.upload_id → data_source_id and update FK."""

    # Note: FK constraint alert_history_upload_id_fkey was already dropped in migration 008
    # to allow dropping the uploads table. We only need to rename the column and create
    # the new FK to data_sources.

    # Rename column
    op.alter_column(
        "alert_history",
        "upload_id",
        new_column_name="data_source_id",
        existing_type=postgresql.UUID(as_uuid=True),
    )

    # Add new FK to data_sources table
    op.create_foreign_key(
        "alert_history_data_source_id_fkey",
        "alert_history",
        "data_sources",
        ["data_source_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Create index (was dropped in migration 008)
    op.create_index(
        "ix_alert_history_data_source_id", "alert_history", ["data_source_id"]
    )


def downgrade() -> None:
    """Reverse: rename data_source_id back to upload_id, restore FK to uploads."""

    op.drop_index(
        "ix_alert_history_data_source_id", table_name="alert_history"
    )
    op.drop_constraint(
        "alert_history_data_source_id_fkey", "alert_history", type_="foreignkey"
    )
    op.alter_column(
        "alert_history",
        "data_source_id",
        new_column_name="upload_id",
        existing_type=postgresql.UUID(as_uuid=True),
    )
    # Note: downgrade cannot restore FK to uploads table (dropped in migration 008)
    op.create_index("ix_alert_history_upload_id", "alert_history", ["upload_id"])
