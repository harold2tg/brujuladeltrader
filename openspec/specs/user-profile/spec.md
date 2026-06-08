# Spec: user-profile

## Capability
User profile management, password change, statistics aggregation, and account deletion for La Brújula del Trader.

## Requirements

### RF-UP-01: Get User Profile
- Endpoint: `GET /users/profile`
- Header: `Authorization: Bearer <access_token>`
- Response: `{ success: true, data: { id, email, name, plan, language, timezone, created_at, is_active } }`
- Notes: Extends existing GET /auth/me, returns same format

### RF-UP-02: Update User Profile
- Endpoint: `PUT /users/profile`
- Header: `Authorization: Bearer <access_token>`
- Body: `{ name?: str, language?: str, timezone?: str }`
- Validation:
  - name: min 1 char, max 100 chars
  - language: must be "es" or "en"
  - timezone: must be valid IANA timezone (e.g., "America/Bogota")
- Response: `{ success: true, data: { updated_user }, message: "Profile updated" }`
- Errors:
  - `422 Unprocessable Entity` if validation fails

### RF-UP-03: Change Password
- Endpoint: `PUT /users/password`
- Header: `Authorization: Bearer <access_token>`
- Body: `{ current_password: str, new_password: str }`
- Validation:
  - current_password must match stored hash
  - new_password: min 8 chars, 1 uppercase, 1 lowercase, 1 number
  - new_password must be different from current_password
- Response: `{ success: true, message: "Password changed" }`
- Errors:
  - `401 Unauthorized` if current password is wrong
  - `422 Unprocessable Entity` if new password validation fails

### RF-UP-04: Get User Stats
- Endpoint: `GET /users/stats`
- Header: `Authorization: Bearer <access_token>`
- Response: `{ success: true, data: { total_uploads, total_trades, total_pnl, win_rate, avg_rr_ratio, best_month, worst_month } }`
- Notes: Aggregates data from all user's uploads and trades

### RF-UP-05: Delete Account
- Endpoint: `DELETE /users/account`
- Header: `Authorization: Bearer <access_token>`
- Body: `{ password: str }` (confirmation)
- Actions:
  1. Verify password
  2. Set is_active = False
  3. Anonymize email: `deleted_{uuid}@deleted.local`
  4. Clear name: "Deleted User"
  5. Keep trades for analytics (anonymized)
- Response: `{ success: true, message: "Account deleted" }`
- Errors:
  - `401 Unauthorized` if password is wrong

## Scenarios

### Scenario 1: Get Profile Success
```
GIVEN an authenticated user
WHEN GET /users/profile
THEN response contains complete user profile
AND password_hash is NOT included
```

### Scenario 2: Update Profile Success
```
GIVEN an authenticated user
WHEN PUT /users/profile with { name: "New Name", language: "en" }
THEN user profile is updated
AND response contains updated user data
```

### Scenario 3: Update Profile Invalid Language
```
GIVEN an authenticated user
WHEN PUT /users/profile with { language: "fr" }
THEN response is 422 Unprocessable Entity
AND error indicates invalid language value
```

### Scenario 4: Change Password Success
```
GIVEN an authenticated user with correct current_password
WHEN PUT /users/password with valid new_password
THEN password is updated
AND old password no longer works for login
```

### Scenario 5: Change Password Wrong Current
```
GIVEN an authenticated user
WHEN PUT /users/password with wrong current_password
THEN response is 401 Unauthorized
AND message is "Current password is incorrect"
```

### Scenario 6: Get Stats Success
```
GIVEN a user with 3 uploads and 150 trades
WHEN GET /users/stats
THEN response contains aggregated statistics
AND total_uploads = 3, total_trades = 150
```

### Scenario 7: Get Stats No Data
```
GIVEN a user with no uploads
WHEN GET /users/stats
THEN response contains zeros for all metrics
```

### Scenario 8: Delete Account Success
```
GIVEN an authenticated user with correct password
WHEN DELETE /users/account
THEN user is deactivated
AND email is anonymized
AND user cannot login anymore
```

### Scenario 9: Delete Account Wrong Password
```
GIVEN an authenticated user
WHEN DELETE /users/account with wrong password
THEN response is 401 Unauthorized
```

## Data Model

No new tables needed. Uses existing `users` table.

```sql
-- Existing users table
-- Soft delete: set is_active = False
-- Anonymize: update email, name
```

## API Response Format

```python
# Success
{ "success": True, "data": { ... }, "message": "Optional description" }

# Error
{ "detail": "Human-readable message", "code": "ERROR_CODE_SNAKE_CASE" }
```

## Dependencies
- auth module (existing User model, password hashing)
- PostgreSQL (user storage)
- Redis (optional: cache stats)

## Acceptance Criteria
- [ ] GET /users/profile returns user without password_hash
- [ ] PUT /users/profile validates language (es/en) and timezone
- [ ] PUT /users/password verifies current password before changing
- [ ] PUT /users/password validates new password strength
- [ ] GET /users/stats aggregates from trades table
- [ ] DELETE /users/account requires password confirmation
- [ ] DELETE /users/account anonymizes user data
- [ ] All endpoints require valid access token
- [ ] Tests pass with >= 80% coverage
