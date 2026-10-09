"""Pydantic schemas for DataSource API."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Response Schemas
# ============================================================================


class DataSourceResponse(BaseModel):
    """Full DataSource response."""

    id: UUID
    user_id: UUID
    broker: str = Field(..., description="Broker identifier: ctrader, metatrader, binance, etc.")
    broker_account_id: str = Field(..., description="Account ID from the broker")
    name: str = Field(..., description="Human-readable name")
    sync_status: str = Field(..., description="Current sync status: idle | syncing | error")
    last_synced_at: Optional[datetime] = Field(None, description="Last successful sync timestamp")
    trade_count: int = Field(..., description="Total number of trades")
    first_trade_at: Optional[datetime] = Field(None, description="Earliest trade timestamp")
    last_trade_at: Optional[datetime] = Field(None, description="Most recent trade timestamp")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DataSourceListResponse(BaseModel):
    """Paginated list of DataSources."""

    items: list[DataSourceResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


# ============================================================================
# Request Schemas
# ============================================================================


class SyncRequest(BaseModel):
    """Request to sync trades from a broker."""

    mode: str = Field(..., description="Sync mode: day | month | year")
    date: str = Field(..., description="Date in YYYY-MM-DD format")


# ============================================================================
# Sync Response Schemas
# ============================================================================


class SyncResponse(BaseModel):
    """Response from triggering a sync operation."""

    data_source_id: UUID
    status: str = Field(..., description="Sync status: processing | completed | error")
    message: Optional[str] = Field(None, description="Status message or error details")
    trades_added: Optional[int] = Field(None, description="Number of trades added (only on completed)")
