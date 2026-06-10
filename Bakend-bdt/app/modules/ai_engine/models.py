"""SQLAlchemy model for AI provider credentials."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class AiCredentials(Base):
    """AI provider credentials (encrypted at rest)."""

    __tablename__ = "ai_credentials"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_ai_credentials_user_provider"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider = Column(String(20), nullable=False)  # claude | openai | gemini | ollama
    api_key_enc = Column(Text)  # AES-256-GCM encrypted (null for ollama)
    base_url = Column(String(500))  # Only for ollama
    model_override = Column(String(100))  # Optional custom model
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
