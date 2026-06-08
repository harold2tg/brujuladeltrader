"""Pydantic schemas for authentication."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str
    name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str


class UserResponse(BaseModel):
    """Schema for user data in responses."""

    id: uuid.UUID
    email: str
    name: str
    plan: str
    language: str
    timezone: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserResponseWithTokens(BaseModel):
    """Schema for user data with tokens (after registration)."""

    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
