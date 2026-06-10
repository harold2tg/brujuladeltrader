"""SQLAlchemy models for cTrader credentials."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class CtraderCredentials(Base):
    """cTrader API credentials (encrypted at rest)."""

    __tablename__ = "ctrader_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    client_id_enc = Column(Text, nullable=False)  # AES-256-GCM encrypted
    client_secret_enc = Column(Text, nullable=False)
    access_token_enc = Column(Text, nullable=False)
    account_id_enc = Column(Text, nullable=False)
    account_name = Column(String(100))  # Not sensitive
    broker_name = Column(String(100))  # Not sensitive
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
