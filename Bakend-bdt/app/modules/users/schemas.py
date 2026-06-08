"""Pydantic schemas for user profile management."""

import re
from typing import Optional

import pytz
from pydantic import BaseModel, field_validator


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""

    name: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name length."""
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError("Name cannot be empty")
            if len(v) > 100:
                raise ValueError("Name must be 100 characters or less")
            return v.strip()
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        """Validate language is es or en."""
        if v is not None and v not in ("es", "en"):
            raise ValueError("Language must be 'es' or 'en'")
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: Optional[str]) -> Optional[str]:
        """Validate timezone is valid IANA timezone."""
        if v is not None and v not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone: {v}")
        return v


class PasswordChange(BaseModel):
    """Schema for changing user password."""

    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v


class AccountDelete(BaseModel):
    """Schema for account deletion confirmation."""

    password: str


class UserStats(BaseModel):
    """Schema for aggregated user statistics."""

    total_uploads: int
    total_trades: int
    total_pnl: float
    win_rate: float
    avg_rr_ratio: Optional[float] = None
    best_month: Optional[float] = None
    worst_month: Optional[float] = None
