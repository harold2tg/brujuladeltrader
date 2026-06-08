# Tasks: users-module

## Review Workload Forecast

| Metric | Value |
|--------|-------|
| Estimated changed lines | ~250 |
| Files to create/modify | 4 |
| Risk level | Low |
| Chained PRs recommended | No (within 400-line budget) |

---

## PR 1: Users Module (~250 lines)

### Task 1.1: Users Schemas
**File**: `app/modules/users/schemas.py`
**Lines**: ~50
**Dependencies**: None

- [ ] `UserProfileUpdate` schema (name, language, timezone optional)
- [ ] `PasswordChange` schema (current_password, new_password)
- [ ] `AccountDelete` schema (password confirmation)
- [ ] `UserStats` schema (aggregated metrics)
- [ ] Validators: language (es/en), timezone (IANA), password strength

### Task 1.2: Users Service
**File**: `app/modules/users/service.py`
**Lines**: ~100
**Dependencies**: 1.1

- [ ] `get_profile(user_id)` → return user without password_hash
- [ ] `update_profile(user_id, data)` → update name/language/timezone
- [ ] `change_password(user_id, data)` → verify current, hash new, save
- [ ] `get_stats(user_id)` → SQL aggregates on uploads + trades
- [ ] `delete_account(user_id, password)` → verify, anonymize, deactivate

### Task 1.3: Users Router
**File**: `app/modules/users/router.py`
**Lines**: ~60
**Dependencies**: 1.2

- [ ] `GET /users/profile` → return current user profile
- [ ] `PUT /users/profile` → update profile fields
- [ ] `PUT /users/password` → change password
- [ ] `GET /users/stats` → return aggregated stats
- [ ] `DELETE /users/account` → soft delete account

### Task 1.4: Register Router
**File**: `app/main.py`
**Lines**: ~5 (modification)
**Dependencies**: 1.3

- [ ] Import users router
- [ ] Register with `app.include_router(users_router)`

---

## PR 2: Tests (~100 lines)

### Task 2.1: Users Tests
**File**: `tests/modules/test_users.py`
**Lines**: ~100
**Dependencies**: 1.3

- [ ] Test get profile success
- [ ] Test update profile success
- [ ] Test update profile invalid language (422)
- [ ] Test update profile invalid timezone (422)
- [ ] Test change password success
- [ ] Test change password wrong current (401)
- [ ] Test get stats with data
- [ ] Test get stats no data
- [ ] Test delete account success
- [ ] Test delete account wrong password (401)

---

## Dependencies Graph

```
1.1 (schemas) ──→ 1.2 (service) ──→ 1.3 (router) ──→ 1.4 (main.py)
                                                  │
                                                  └──→ 2.1 (tests)
```

## Commit Strategy

### PR 1 Commits
1. `feat(users): add user profile schemas`
2. `feat(users): add user service with profile, password, stats, delete`
3. `feat(users): add users router with all endpoints`
4. `feat(users): register users router in main app`

### PR 2 Commits
1. `test(users): add user endpoint tests`

## Validation Commands

```bash
# Run tests
docker compose -f docker-compose.dev.yml run --rm test pytest tests/modules/test_users.py -v

# Run all tests
docker compose -f docker-compose.dev.yml run --rm test pytest tests/ -v
```
