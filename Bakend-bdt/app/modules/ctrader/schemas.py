"""Pydantic schemas for cTrader endpoints."""

from datetime import datetime

from pydantic import BaseModel


class CredentialsCreate(BaseModel):
    """Request to store cTrader credentials."""
    client_id: str
    client_secret: str
    access_token: str
    account_id: str


class CredentialsResponse(BaseModel):
    """Response after storing credentials."""
    connected: bool
    account_name: str | None = None
    broker: str | None = None


class TestResponse(BaseModel):
    """Response from connection test."""
    connected: bool
    latency_ms: int
    error: str | None = None


class SyncRequest(BaseModel):
    """Request to start trade sync."""
    mode: str  # "day" | "month" | "year"
    date: str  # YYYY-MM-DD


class SyncResponse(BaseModel):
    """Response after starting sync."""
    job_id: str
    status: str = "processing"
    estimated_trades: int = 0


class SyncStatusResponse(BaseModel):
    """Response for sync status polling."""
    status: str
    progress_pct: float = 0.0
    trades_imported: int = 0
    error: str | None = None
