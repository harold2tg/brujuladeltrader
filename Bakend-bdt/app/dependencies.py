"""FastAPI dependencies for dependency injection."""

import redis.asyncio as redis
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.modules.auth.models import User
from app.modules.auth.service import AuthService, decode_token
from app.shared.exceptions import UnauthorizedException


async def get_redis() -> redis.Redis:
    """Dependency that provides a Redis client."""
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency that extracts and validates the current user from the Authorization header."""
    token = authorization.replace("Bearer ", "")
    if not token:
        raise UnauthorizedException("Missing authorization token")

    # Decode token
    payload = decode_token(token)

    # Check token type
    if payload.get("type") == "refresh":
        raise UnauthorizedException("Invalid token type")

    # Check blacklist
    jti = payload.get("jti")
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    if jti and await redis_client.get(f"blacklist:{jti}"):
        raise UnauthorizedException("Token has been revoked")

    # Load user
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("User not found")

    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that ensures the current user is active."""
    if not current_user.is_active:
        raise UnauthorizedException("Account is deactivated")
    return current_user
