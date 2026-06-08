"""Pydantic schemas for parser module."""

from typing import Optional

from pydantic import BaseModel


class ParseResult(BaseModel):
    """Schema for parse result response."""

    status: str
    total_trades: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    error_message: Optional[str] = None
