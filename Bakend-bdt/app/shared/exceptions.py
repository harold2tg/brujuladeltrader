"""Custom HTTP exceptions for La Brújula del Trader."""

from fastapi import HTTPException


class BadRequestException(HTTPException):
    """400 Bad Request - Invalid input."""

    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=400, detail=detail)


class ConflictException(HTTPException):
    """409 Conflict - Resource already exists."""

    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=409, detail=detail)


class UnauthorizedException(HTTPException):
    """401 Unauthorized - Authentication required or failed."""

    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(status_code=401, detail=detail)


class ForbiddenException(HTTPException):
    """403 Forbidden - Insufficient permissions."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=403, detail=detail)


class NotFoundException(HTTPException):
    """404 Not Found - Resource not found."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class PlanLimitException(HTTPException):
    """403 Forbidden - Plan limit exceeded."""

    def __init__(self, detail: str = "Plan limit exceeded"):
        super().__init__(status_code=403, detail=detail)
