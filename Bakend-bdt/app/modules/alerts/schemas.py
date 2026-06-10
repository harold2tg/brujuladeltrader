"""Pydantic schemas for alerts module."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator


class RuleCreate(BaseModel):
    """Schema for creating an alert rule."""

    alert_type: str
    threshold: Decimal
    is_active: bool = True


class RuleUpdate(BaseModel):
    """Schema for updating an alert rule."""

    threshold: Decimal | None = None
    is_active: bool | None = None


class RuleResponse(BaseModel):
    """Alert rule response."""

    id: str
    user_id: str
    alert_type: str
    threshold: Decimal
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("id", "user_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        return str(v) if v is not None else v


class HistoryResponse(BaseModel):
    """Alert history entry response."""

    id: str
    user_id: str
    rule_id: str
    upload_id: str | None
    triggered_value: Decimal
    triggered_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("id", "user_id", "rule_id", "upload_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        return str(v) if v is not None else v


class PaginatedHistory(BaseModel):
    """Paginated list of alert history entries."""

    items: list[HistoryResponse]
    total: int
    page: int
    limit: int
    pages: int
