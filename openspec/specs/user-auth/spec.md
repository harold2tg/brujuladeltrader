# Spec: user-auth

## Capability
User authentication and authorization for La Brújula del Trader. JWT-based with bcrypt password hashing and Redis token blacklist.

## Requirements

### RF-AUTH-01: User Registration
- Endpoint: `POST /auth/register`
- Body: `{ email: str, password: str, name: str }`
- Password validation: minimum 8 characters, at least 1 uppercase, 1 lowercase, 1 number
- Email validation: valid format, unique in database
- Password hashing: bcrypt with cost factor >= 12
- Response: `{ success: true, data: { user, access_token, refresh_token } }`
- Errors:
  - `409 Conflict` if email already exists
  - `422 Unprocessable Entity` if validation fails

### RF-AUTH-02: User Login
- Endpoint: `POST /auth/login`
- Body: `{ email: str, password: str }`
- Verification: bcrypt.checkpw against stored hash
- JWT generation:
  - Access token: 24 hours, contains `sub` (user_id), `exp`, `iat`, `jti`
  - Refresh token: 30 days, contains `sub` (user_id), `exp`, `iat`, `jti`, `type: "refresh"`
- Response: `{ success: true, data: { access_token, refresh_token } }`
- Errors:
  - `401 Unauthorized` with generic message "Invalid credentials" (never reveal if email exists)

### RF-AUTH-03: Token Refresh
- Endpoint: `POST /auth/refresh`
- Body: `{ refresh_token: str }`
- Validation: verify JWT signature, check not expired, check jti not blacklisted
- Response: `{ success: true, data: { access_token } }`
- Errors:
  - `401 Unauthorized` if token invalid or expired

### RF-AUTH-04: User Logout
- Endpoint: `POST /auth/logout`
- Header: `Authorization: Bearer <access_token>`
- Action: store jti in Redis with TTL = remaining token time
- Response: `204 No Content`
- After logout: any request with this token returns `401 Unauthorized`

### RF-AUTH-05: Get Current User
- Endpoint: `GET /auth/me`
- Header: `Authorization: Bearer <access_token>`
- Response: `{ success: true, data: { id, email, name, plan, language, timezone, created_at } }`
- Errors:
  - `401 Unauthorized` if token invalid or expired

## Scenarios

### Scenario 1: Successful Registration
```
GIVEN a new user with email "trader@example.com"
WHEN POST /auth/register with valid data
THEN user is created in database with hashed password
AND response contains access_token and refresh_token
AND password is NOT stored in plaintext
```

### Scenario 2: Duplicate Email Registration
```
GIVEN an existing user with email "trader@example.com"
WHEN POST /auth/register with same email
THEN response is 409 Conflict
AND error message does not reveal that email already exists
```

### Scenario 3: Successful Login
```
GIVEN a registered user with correct credentials
WHEN POST /auth/login with valid email and password
THEN response contains access_token (24h) and refresh_token (30d)
AND tokens contain correct user_id in sub claim
```

### Scenario 4: Invalid Credentials Login
```
GIVEN a registered user
WHEN POST /auth/login with wrong password
THEN response is 401 Unauthorized
AND message is generic "Invalid credentials"
AND system does NOT indicate whether email exists
```

### Scenario 5: Token Refresh
```
GIVEN a user with valid refresh_token
WHEN POST /auth/refresh with the token
THEN response contains new access_token
AND old refresh_token remains valid
```

### Scenario 6: Expired Refresh Token
```
GIVEN a user with expired refresh_token
WHEN POST /auth/refresh with the token
THEN response is 401 Unauthorized
```

### Scenario 7: Logout Blacklists Token
```
GIVEN a user with valid access_token
WHEN POST /auth/logout
THEN jti is stored in Redis with TTL = remaining token time
AND subsequent requests with that token return 401
```

### Scenario 8: Get Current User
```
GIVEN a user with valid access_token
WHEN GET /auth/me
THEN response contains user profile (without password_hash)
AND email, name, plan, language, timezone are present
```

### Scenario 9: Get Current User with Invalid Token
```
GIVEN a request with expired or invalid token
WHEN GET /auth/me
THEN response is 401 Unauthorized
```

## Data Model

```sql
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name          VARCHAR(100) NOT NULL,
    plan          VARCHAR(20) NOT NULL DEFAULT 'free',
    language      VARCHAR(10) NOT NULL DEFAULT 'es',
    timezone      VARCHAR(50) NOT NULL DEFAULT 'America/Bogota',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active     BOOLEAN NOT NULL DEFAULT TRUE
);
```

## API Response Format

```python
# Success
{ "success": True, "data": { ... }, "message": "Optional description" }

# Error
{ "detail": "Human-readable message", "code": "ERROR_CODE_SNAKE_CASE" }
```

## Dependencies
- PostgreSQL 15 (user storage)
- Redis 7 (JWT blacklist)
- python-jose (JWT signing/verification)
- bcrypt (password hashing)
- pydantic-settings (configuration)

## Acceptance Criteria
- [ ] All endpoints are async def
- [ ] Passwords hashed with bcrypt cost >= 12
- [ ] JWT access token expires in 24 hours
- [ ] JWT refresh token expires in 30 days
- [ ] Logout blacklists token jti in Redis
- [ ] Login errors always return 401 generic message
- [ ] Duplicate email returns 409
- [ ] Email field has unique constraint
- [ ] Tests pass with >= 80% coverage
