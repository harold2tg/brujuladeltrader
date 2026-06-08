"""Trade model for parsed trade data."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Trade(Base):
    """Trade model for storing parsed trade data."""

    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(UUID(as_uuid=True), ForeignKey("uploads.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=False)
    entry_price = Column(Numeric(12, 5), nullable=False)
    close_price = Column(Numeric(12, 5), nullable=False)
    lot_size = Column(Numeric(8, 4), nullable=True)
    net_pnl = Column(Numeric(10, 2), nullable=False)
    balance = Column(Numeric(10, 2), nullable=True)
    hour_of_day = Column(SmallInteger, nullable=False)
    day_of_week = Column(SmallInteger, nullable=False)
    week_of_year = Column(SmallInteger, nullable=False)
    month = Column(SmallInteger, nullable=False)
    year = Column(SmallInteger, nullable=False)
    session = Column(String(20), nullable=False)
    is_winner = Column(Boolean, nullable=False)
    trade_number = Column(Integer, nullable=False)

    # Relationships
    upload = relationship("Upload", backref="trades")
    user = relationship("User", backref="trades")
