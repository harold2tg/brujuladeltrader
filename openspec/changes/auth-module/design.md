# Design: auth-module

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI App                             │
├─────────────────────────────────────────────────────────────┤
│  main.py (CORS, middleware, router registration)            │
├─────────────────────────────────────────────────────────────┤
│  dependencies.py                                            │
│  ├── get_db() → AsyncSession                                │
│  ├── get_current_user(token) → User                         │
│  └── get_current_active_user(user) → User                   │
├─────────────────────────────────────────────────────────────┤
│  modules/auth/                                              │
│  ├── router.py (endpoints)                                  │
│  ├── service.py (business logic)                            │
│  ├── schemas.py (Pydantic models)                           │
│  └── models.py (SQLAlchemy User model)                      │
├─────────────────────────────────────────────────────────────┤
│  shared/                                                    │
│  ├── exceptions.py (HTTPException wrappers)                 │
│  └── responses.py (standard response format)                │
├─────────────────────────────────────────────────────────────┤
│  config.py (pydantic-settings)                              │
│  database.py (async engine + session)                       │
└─────────────────────────────────────────────────────────────┘
         │                           │
         ▼                           ▼
┌─────────────────┐        ┌─────────────────┐
│   PostgreSQL    │        │     Redis       │
│  (users table)  │        │ (JWT blacklist) │
└─────────────────┘        └─────────────────┘
```

## File Structure

```
brujula-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── modules/
│   │   ├── __init__.py
│   │   └── auth/
│   │       ├── __init__.py
│   │       ├── router.py
│   │       ├── service.py
│   │       ├── schemas.py
│   │       └── models.py
│   └── shared/
│       ├── __init__.py
│       ├── exceptions.py
│       └── responses.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── modules/
│       ├── __init__.py
│       └── test_auth.py
├── alembic/
│   └── env.py
├── alembic.ini
├── pyproject.toml
├── .env.example
└── docker/
    ├── Dockerfile
    └── Dockerfile.dev
```

## Data Flow

### Registration Flow
```
Client → POST /auth/register
  │
  ├─→ Validate email format (Pydantic)
  ├─→ Check email uniqueness (DB query)
  ├─→ Hash password (bcrypt cost=12)
  ├─→ Insert user (DB)
  ├─→ Generate JWT access token (24h)
  ├─→ Generate JWT refresh token (30d)
  └─→ Return { user, access_token, refresh_token }
```

### Login Flow
```
Client → POST /auth/login
  │
  ├─→ Find user by email (DB query)
  ├─→ If not found → return 401 "Invalid credentials"
  ├─→ Verify password (bcrypt.checkpw)
  ├─→ If invalid → return 401 "Invalid credentials"
  ├─→ Generate JWT access token (24h)
  ├─→ Generate JWT refresh token (30d)
  └─→ Return { access_token, refresh_token }
```

### Authenticated Request Flow
```
Client → GET /auth/me (Header: Bearer <token>)
  │
  ├─→ Extract token from header
  ├─→ Decode JWT (verify signature + expiry)
  ├─→ Check jti not in Redis blacklist
  ├─→ Load user from DB
  ├─→ Check user.is_active
  └─→ Return user profile
```

### Logout Flow
```
Client → POST /auth/logout (Header: Bearer <token>)
  │
  ├─→ Decode JWT to get jti + exp
  ├─→ Calculate remaining TTL
  ├─→ Store jti in Redis with TTL
  └─→ Return 204 No Content
```

## Key Implementation Details

### config.py
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ENCRYPTION_KEY: str  # For cTrader + AI credentials

    class Config:
        env_file = ".env"

settings = Settings()
```

### database.py
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(settings.DATABASE_URL, echo=settings.APP_ENV == "development")
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

### JWT Token Structure
```python
# Access token payload
{
    "sub": "user-uuid",
    "exp": datetime.utcnow() + timedelta(hours=24),
    "iat": datetime.utcnow(),
    "jti": "unique-token-id"
}

# Refresh token payload
{
    "sub": "user-uuid",
    "exp": datetime.utcnow() + timedelta(days=30),
    "iat": datetime.utcnow(),
    "jti": "unique-token-id",
    "type": "refresh"
}
```

### Redis Blacklist
```
Key: blacklist:{jti}
TTL: remaining token time (calculated from exp - now)
Value: "1" (exists = blacklisted)
```

## Dependencies (pyproject.toml)

```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.110.0"
uvicorn = {extras = ["standard"], version = "^0.29.0"}
sqlalchemy = {extras = ["asyncio"], version = "^2.0.0"}
asyncpg = "^0.29.0"
alembic = "^1.13.0"
pydantic = {extras = ["email"], version = "^2.0.0"}
pydantic-settings = "^2.0.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
bcrypt = "^4.1.0"
redis = {extras = ["hiredis"], version = "^5.0.0"}
python-multipart = "^0.0.9"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
httpx = "^0.27.0"
```

## Security Considerations

1. **Password Storage**: bcrypt with cost=12, never store plaintext
2. **JWT Secret**: minimum 32 characters, loaded from env
3. **Token Blacklist**: Redis with TTL matching token expiry
4. **Error Messages**: generic "Invalid credentials" for login failures
5. **Email Uniqueness**: DB constraint + application-level check
6. **CORS**: configured for frontend origins only

## Testing Strategy

- Unit tests for service layer (mock DB + Redis)
- Integration tests for endpoints (httpx AsyncClient)
- Test database: separate PostgreSQL instance
- Fixtures: test user, test tokens, mock Redis

## Rollback Plan

1. Delete all created files
2. Drop users table (if migration was applied)
3. Remove Redis blacklist keys
4. No external dependencies to clean up
