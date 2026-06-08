"""Authentication router."""

import redis.asyncio as redis
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.modules.auth.schemas import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserResponseWithTokens,
)
from app.modules.auth.service import AuthService
from app.shared.responses import success_response

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_redis() -> redis.Redis:
    """Dependency that provides a Redis client."""
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> AuthService:
    """Dependency that provides an AuthService instance."""
    return AuthService(db, redis_client)


@router.post("/register", response_model=dict)
async def register(
    data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user."""
    result = await auth_service.register(data)
    return success_response(
        data={
            "user": UserResponse.model_validate(result["user"]),
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer",
        },
        message="User registered successfully",
    )


@router.post("/login", response_model=dict)
async def login(
    data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate a user and return tokens."""
    result = await auth_service.login(data)
    return success_response(
        data=TokenResponse(**result),
        message="Login successful",
    )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh an access token."""
    result = await auth_service.refresh_token(data.refresh_token)
    return success_response(
        data=TokenResponse(access_token=result["access_token"], refresh_token=""),
        message="Token refreshed successfully",
    )


@router.post("/logout", status_code=204)
async def logout(
    authorization: str = Header(...),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Logout by blacklisting the current token."""
    token = authorization.replace("Bearer ", "")
    await auth_service.logout(token)
    return None


@router.get("/me", response_model=dict)
async def get_me(
    authorization: str = Header(...),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get the current authenticated user."""
    token = authorization.replace("Bearer ", "")
    user = await auth_service.get_current_user(token)
    return success_response(
        data=UserResponse.model_validate(user),
    )
