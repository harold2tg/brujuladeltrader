"""Standard response formats for La Brújula del Trader."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response format."""

    success: bool = True
    data: T
    message: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response format."""

    detail: str
    code: str


def success_response(data: Any, message: str | None = None) -> dict:
    """Create a success response."""
    return {"success": True, "data": data, "message": message}


def error_response(detail: str, code: str) -> dict:
    """Create an error response."""
    return {"detail": detail, "code": code}
