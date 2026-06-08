"""Test fixtures for authentication tests."""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
import redis.asyncio as redis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.modules.auth.models import User
from app.modules.auth.service import hash_password
from app.modules.parser.models import Trade

# Test engine and session factory (uses Docker services)
test_engine = create_async_engine(settings.DATABASE_URL, echo=True)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session for tests."""
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[redis.Redis, None]:
    """Provide a Redis client for tests."""
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    yield client
    await client.flushall()
    await client.aclose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, redis_client: redis.Redis) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP test client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=hash_password("TestPass123"),
        name="Test Trader",
        plan="free",
        language="es",
        timezone="America/Bogota",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def test_user_tokens(test_user: User) -> dict[str, str]:
    """Get tokens for the test user."""
    from app.modules.auth.service import create_access_token, create_refresh_token

    access_token, _, _ = create_access_token(str(test_user.id))
    refresh_token, _, _ = create_refresh_token(str(test_user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
