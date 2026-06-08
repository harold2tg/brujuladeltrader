# Proposal: auth-module

## Intent

La Brújula del Trader necesita autenticación para proteger datos sensibles de trading (credenciales cTrader, historial de operaciones). Sin auth, no hay forma de asociar usuarios con sus datos ni de implementar planes Free/Pro.

## Scope

### In Scope
- User registration with email, password, name
- Login with JWT (access + refresh tokens)
- Logout with token blacklist in Redis
- Token refresh endpoint
- Get current user profile (/auth/me)
- Password hashing with bcrypt (cost >= 12)
- Email uniqueness validation (409 on duplicate)
- Generic login errors (never reveal if email exists)

### Out of Scope
- User profile editing (users module - next phase)
- Password reset via email
- OAuth/Google login
- Rate limiting (infra concern)
- Email verification

## Capabilities

### New Capabilities
- `user-auth`: Registration, login, logout, token refresh, current user retrieval

### Modified Capabilities
- None (first module)

## Approach

1. **config.py**: Pydantic Settings reading from .env (DATABASE_URL, REDIS_URL, JWT_SECRET_KEY, etc.)
2. **database.py**: SQLAlchemy async engine + session factory + Base declarative
3. **modules/auth/models.py**: User table (UUID PK, email unique, password_hash, name, plan, language, timezone, timestamps, is_active)
4. **modules/auth/schemas.py**: Pydantic models for request/response (UserCreate, UserLogin, TokenResponse, UserResponse)
5. **modules/auth/service.py**: Business logic - register (bcrypt hash), login (verify password, create JWT), logout (blacklist jti in Redis), refresh (verify refresh token, issue new access), get_me
6. **modules/auth/router.py**: FastAPI router with all endpoints
7. **shared/exceptions.py**: Custom HTTP exceptions
8. **shared/responses.py**: Standard response wrapper { success, data, message }
9. **dependencies.py**: get_db, get_current_user, get_current_active_user
10. **main.py**: FastAPI app initialization, CORS, router registration

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/main.py` | New | FastAPI app entry point |
| `app/config.py` | New | Environment settings |
| `app/database.py` | New | Async DB connection |
| `app/dependencies.py` | New | FastAPI dependencies |
| `app/modules/auth/` | New | Complete auth module |
| `app/shared/` | New | Shared utilities |
| `tests/modules/test_auth.py` | New | Auth tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Redis not available for blacklist | Low | Use fallback: store in memory (dev only) with warning |
| JWT secret weak | Medium | Validate minimum 32 chars in config, fail fast on startup |
| bcrypt too slow on register | Low | Cost factor 12 is acceptable for auth endpoints |

## Rollback Plan

Delete all created files. No database migrations yet (first module). Remove Engram observation.

## Dependencies

- PostgreSQL 15 (for user storage)
- Redis 7 (for JWT blacklist)
- Python packages: fastapi, sqlalchemy, asyncpg, python-jose, bcrypt, pydantic-settings

## Success Criteria

- [ ] POST /auth/register creates user with hashed password, returns tokens
- [ ] POST /auth/login returns access + refresh tokens for valid credentials
- [ ] POST /auth/login returns 400 with generic message for invalid credentials
- [ ] POST /auth/refresh issues new access token
- [ ] POST /auth/logout blacklists token in Redis
- [ ] GET /auth/me returns current user with valid token
- [ ] GET /auth/me returns 401 with invalid/expired token
- [ ] Duplicate email returns 409 Conflict
- [ ] All endpoints are async def
- [ ] Tests pass with >= 80% coverage
