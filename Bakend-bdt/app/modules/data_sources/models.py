"""DataSource model for broker trade data management."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
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
