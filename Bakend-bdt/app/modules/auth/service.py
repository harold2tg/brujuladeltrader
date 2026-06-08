"""Authentication service with JWT and Redis blacklist."""

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import redis.asyncio as redis
from fastapi import Depends
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate, UserLogin
from app.shared.exceptions import ConflictException, UnauthorizedException


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with cost factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: str) -> tuple[str, str, datetime]:
    """Create a JWT access token. Returns (token, jti, expiry)."""
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": jti,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expire


def create_refresh_token(user_id: str) -> tuple[str, str, datetime]:
    """Create a JWT refresh token. Returns (token, jti, expiry)."""
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": jti,
        "type": "refresh",
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expire


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token. Raises JWTError if invalid."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise UnauthorizedException("Invalid or expired token")


class AuthService:
    """Authentication service for user management and JWT operations."""

    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client

    async def register(self, data: UserCreate) -> dict:
        """Register a new user."""
        # Check email uniqueness
        result = await self.db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise ConflictException("Email already registered")

        # Create user
        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            name=data.name,
        )
        self.db.add(user)
        await self.db.flush()  # Get the ID without committing

        # Generate tokens
        access_token, access_jti, access_exp = create_access_token(str(user.id))
        refresh_token, refresh_jti, refresh_exp = create_refresh_token(str(user.id))

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    async def login(self, data: UserLogin) -> dict:
        """Authenticate a user and return tokens."""
        # Find user by email
        result = await self.db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        # Generic error message (never reveal if email exists)
        if not user or not verify_password(data.password, user.password_hash):
            raise UnauthorizedException("Invalid credentials")

        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")

        # Generate tokens
        access_token, access_jti, access_exp = create_access_token(str(user.id))
        refresh_token, refresh_jti, refresh_exp = create_refresh_token(str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh an access token using a valid refresh token."""
        # Decode refresh token
        payload = decode_token(refresh_token)

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")

        user_id = payload.get("sub")
        jti = payload.get("jti")

        # Check if token is blacklisted
        if jti and await self.redis.get(f"blacklist:{jti}"):
            raise UnauthorizedException("Token has been revoked")

        # Check if user exists and is active
        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        # Generate new access token
        access_token, _, _ = create_access_token(user_id)

        return {"access_token": access_token}

    async def logout(self, token: str) -> None:
        """Logout by blacklisting the current access token."""
        payload = decode_token(token)
        jti = payload.get("jti")
        exp = payload.get("exp")

        if jti and exp:
            # Calculate remaining TTL
            expire_time = datetime.fromtimestamp(exp, tz=timezone.utc)
            remaining_ttl = int((expire_time - datetime.now(timezone.utc)).total_seconds())

            if remaining_ttl > 0:
                await self.redis.setex(f"blacklist:{jti}", remaining_ttl, "1")

    async def get_current_user(self, token: str) -> User:
        """Get the current user from a valid access token."""
        payload = decode_token(token)

        # Verify it's an access token (not refresh)
        if payload.get("type") == "refresh":
            raise UnauthorizedException("Invalid token type")

        jti = payload.get("jti")

        # Check if token is blacklisted
        if jti and await self.redis.get(f"blacklist:{jti}"):
            raise UnauthorizedException("Token has been revoked")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")

        # Load user
        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise UnauthorizedException("User not found")

        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")

        return user
