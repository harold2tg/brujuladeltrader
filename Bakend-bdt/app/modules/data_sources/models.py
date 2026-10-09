"""DataSource and Trade models for broker trade data management."""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class DataSource(Base):
    """DataSource represents a broker account from which trades are synced.

    Replaces the Upload model for broker integrations. Each DataSource
    represents a unique broker account (e.g., one cTrader account, one
    MetaTrader account, etc.) and contains all trades synced from that broker.
    """

    __tablename__ = "data_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Broker identification
    broker = Column(String(50), nullable=False, comment="Broker identifier: ctrader, metatrader, binance, etc.")
    broker_account_id = Column(String(200), nullable=False, comment="Account ID from the broker")
    name = Column(String(200), nullable=False, comment="Human-readable name, e.g., 'cTrader - Live Account'")

    # Sync state
    sync_status = Column(String(20), nullable=False, default="idle", comment="idle | syncing | error")
    last_synced_at = Column(DateTime(timezone=True), nullable=True, comment="Last successful sync timestamp")

    # Trade metadata (cached for quick queries)
    trade_count = Column(Integer, nullable=False, default=0, comment="Total number of trades in this data source")
    first_trade_at = Column(DateTime(timezone=True), nullable=True, comment="Timestamp of the earliest trade")
    last_trade_at = Column(DateTime(timezone=True), nullable=True, comment="Timestamp of the most recent trade")

    # Extensibility
    metadata_ = Column("metadata", JSON, nullable=False, default=dict, comment="Broker-specific extra data")

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="data_sources")
    trades = relationship("Trade", backref="data_source", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "broker", "broker_account_id", name="uq_user_broker_account"),
    )

    def __repr__(self) -> str:
        return f"<DataSource {self.broker}:{self.broker_account_id} ({self.trade_count} trades)>"


class Trade(Base):
    """Trade model for storing parsed trade data."""

    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=False)
    entry_price = Column(Numeric(16, 5), nullable=False)
    close_price = Column(Numeric(16, 5), nullable=False)
    lot_size = Column(Numeric(12, 4), nullable=True)
    net_pnl = Column(Numeric(14, 2), nullable=False)
    balance = Column(Numeric(14, 2), nullable=True)
    hour_of_day = Column(SmallInteger, nullable=False)
    day_of_week = Column(SmallInteger, nullable=False)
    week_of_year = Column(SmallInteger, nullable=False)
    month = Column(SmallInteger, nullable=False)
    year = Column(SmallInteger, nullable=False)
    session = Column(String(20), nullable=False)
    is_winner = Column(Boolean, nullable=False)
    trade_number = Column(Integer, nullable=False)
    deal_id = Column(String(100), nullable=True)  # cTrader deal ID for idempotency

    # Relationships
    user = relationship("User", backref="trades")
