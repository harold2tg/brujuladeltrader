# Tasks: auth-module

## Review Workload Forecast

| Metric | Value |
|--------|-------|
| Estimated changed lines | ~450 |
| Files to create/modify | 12 |
| Risk level | Medium |
| Chained PRs recommended | Yes (budget: 400 lines) |

**Decision needed**: This change exceeds the 400-line review budget. Options:
1. Split into 2 chained PRs (recommended)
2. Proceed with single PR + size exception

---

## PR 1: Foundation + Core Auth (~380 lines)

### Task 1.1: Project Setup
**Files**: `pyproject.toml`, `.env.example`, `app/__init__.py`
**Lines**: ~50
**Dependencies**: None

- [ ] Create `pyproject.toml` with all dependencies
- [ ] Create `.env.example` with required variables
- [ ] Create `app/__init__.py`

### Task 1.2: Configuration
**File**: `app/config.py`
**Lines**: ~30
**Dependencies**: 1.1

- [ ] Implement `Settings` class with pydantic-settings
- [ ] Load all env vars: DATABASE_URL, REDIS_URL, JWT_SECRET_KEY, etc.
- [ ] Add validation for JWT_SECRET_KEY (min 32 chars)

### Task 1.3: Database
**File**: `app/database.py`
**Lines**: ~35
**Dependencies**: 1.2

- [ ] Create async engine from DATABASE_URL
- [ ] Create async session factory
- [ ] Create `Base` declarative class
- [ ] Implement `get_db()` dependency

### Task 1.4: Shared Utilities
**Files**: `app/shared/exceptions.py`, `app/shared/responses.py`
**Lines**: ~40
**Dependencies**: None

- [ ] Create custom HTTP exceptions (409 Conflict, 401 Unauthorized, etc.)
- [ ] Implement standard response wrapper `{ success, data, message }`
- [ ] Implement error response format `{ detail, code }`

### Task 1.5: User Model
**File**: `app/modules/auth/models.py`
**Lines**: ~35
**Dependencies**: 1.3

- [ ] Define `User` SQLAlchemy model
- [ ] Fields: id (UUID), email (unique), password_hash, name, plan, language, timezone, timestamps, is_active
- [ ] Add table constraints

### Task 1.6: Auth Schemas
**File**: `app/modules/auth/schemas.py`
**Lines**: ~50
**Dependencies**: None

- [ ] `UserCreate` schema (email, password, name)
- [ ] `UserLogin` schema (email, password)
- [ ] `TokenResponse` schema (access_token, refresh_token)
- [ ] `UserResponse` schema (id, email, name, plan, language, timezone, created_at)
- [ ] Password validation (min 8, 1 upper, 1 lower, 1 number)

### Task 1.7: Auth Service
**File**: `app/modules/auth/service.py`
**Lines**: ~120
**Dependencies**: 1.5, 1.6

- [ ] `register()`: validate email uniqueness, hash password, insert user, generate tokens
- [ ] `login()`: find user by email, verify password, generate tokens
- [ ] `refresh_token()`: verify refresh token, generate new access token
- [ ] `logout()`: decode token, store jti in Redis with TTL
- [ ] `get_current_user()`: verify token, check blacklist, load user
- [ ] Helper: `create_access_token()`, `create_refresh_token()`
- [ ] Helper: `hash_password()`, `verify_password()`

### Task 1.8: Auth Router
**File**: `app/modules/auth/router.py`
**Lines**: ~60
**Dependencies**: 1.7

- [ ] `POST /auth/register` → service.register()
- [ ] `POST /auth/login` → service.login()
- [ ] `POST /auth/refresh` → service.refresh_token()
- [ ] `POST /auth/logout` → service.logout()
- [ ] `GET /auth/me` → service.get_current_user()

### Task 1.9: Dependencies
**File**: `app/dependencies.py`
**Lines**: ~30
**Dependencies**: 1.7

- [ ] `get_db()` → from database.py
- [ ] `get_current_user()` → from auth service
- [ ] `get_current_active_user()` → check is_active

### Task 1.10: Main App
**File**: `app/main.py`
**Lines**: ~35
**Dependencies**: 1.8, 1.9

- [ ] Create FastAPI app instance
- [ ] Configure CORS middleware
- [ ] Register auth router
- [ ] Add health check endpoint

---

## PR 2: Tests + Alembic (~120 lines)

### Task 2.1: Alembic Setup
**Files**: `alembic.ini`, `alembic/env.py`
**Lines**: ~30
**Dependencies**: 1.3

- [ ] Configure alembic.ini for async PostgreSQL
- [ ] Set up env.py with async engine
- [ ] Generate initial migration for users table

### Task 2.2: Test Fixtures
**File**: `tests/conftest.py`
**Lines**: ~40
**Dependencies**: 1.3

- [ ] Create test database session fixture
- [ ] Create test client fixture (httpx AsyncClient)
- [ ] Create test user fixture
- [ ] Create Redis mock fixture

### Task 2.3: Auth Tests
**File**: `tests/modules/test_auth.py`
**Lines**: ~80
**Dependencies**: 2.1, 2.2

- [ ] Test register success
- [ ] Test register duplicate email (409)
- [ ] Test register invalid data (422)
- [ ] Test login success
- [ ] Test login invalid credentials (401)
- [ ] Test refresh success
- [ ] Test refresh expired token (401)
- [ ] Test logout blacklists token
- [ ] Test get current user success
- [ ] Test get current user invalid token (401)

---

## Dependencies Graph

```
1.1 (setup) ──→ 1.2 (config) ──→ 1.3 (database) ──→ 1.5 (models) ──→ 1.7 (service) ──→ 1.8 (router) ──→ 1.10 (main)
                    │                                    │
                    └──→ 1.4 (shared)                    └──→ 1.6 (schemas) ──→ 1.7 (service)
                                                                                          │
                                                                                          ▼
                                                                              1.9 (dependencies) ──→ 1.10 (main)

1.3 (database) ──→ 2.1 (alembic) ──→ 2.3 (tests)
1.3 (database) ──→ 2.2 (fixtures) ──→ 2.3 (tests)
```

## Commit Strategy

### PR 1 Commits (Foundation + Core Auth)
1. `feat(auth): add project setup with dependencies`
2. `feat(auth): add config and database modules`
3. `feat(auth): add shared utilities (exceptions, responses)`
4. `feat(auth): add User model and schemas`
5. `feat(auth): add auth service with JWT logic`
6. `feat(auth): add auth router with endpoints`
7. `feat(auth): add FastAPI main app`

### PR 2 Commits (Tests + Alembic)
1. `feat(auth): add Alembic setup and initial migration`
2. `test(auth): add test fixtures and auth tests`

## Validation Commands

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest tests/ -v --cov=app --cov-report=html

# Check coverage
poetry run pytest tests/ --cov=app --cov-report=term-missing

# Run linter
poetry run ruff check app/

# Run type checker
poetry run mypy app/
```
