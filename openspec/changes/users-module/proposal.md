# Proposal: users-module

## Intent

El módulo users permite a los traders gestionar su perfil, cambiar contraseña y ver estadísticas agregadas de sus operaciones. Es necesario para completar la experiencia de usuario antes de avanzar a uploads y analytics.

## Scope

### In Scope
- Get user profile (extiende GET /auth/me existente)
- Update user profile (name, language, timezone)
- Change password (verifica contraseña actual)
- Get user stats (métricas agregadas de uploads)
- Delete account (soft delete)

### Out of Scope
- Upload management (módulo uploads)
- AI credentials management (módulo ai_engine)
- Notification preferences
- Two-factor authentication

## Capabilities

### New Capabilities
- `user-profile`: Profile viewing and editing
- `user-password`: Password change with current password verification
- `user-stats`: Aggregated trading statistics
- `user-account`: Account deletion (soft delete)

### Modified Capabilities
- None (auth module already handles registration and login)

## Approach

1. Create `modules/users/router.py` with all endpoints
2. Create `modules/users/service.py` with business logic
3. Create `modules/users/schemas.py` with Pydantic models
4. Reuse existing `User` model from auth module
5. Add stats aggregation using SQL queries on trades table
6. Implement soft delete (set is_active=False, anonymize data)

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/modules/users/` | New | Complete users module |
| `app/main.py` | Modified | Register users router |
| `tests/modules/test_users.py` | New | Users endpoint tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Stats query performance | Low | Use SQL aggregates, cache in Redis |
| Soft delete data leak | Medium | Anonymize email, keep minimal data |

## Rollback Plan

Delete users module files. No database changes needed (uses existing users table).

## Dependencies

- auth module (already implemented)
- PostgreSQL (user storage)
- Redis (caching stats)

## Success Criteria

- [ ] GET /users/profile returns complete user profile
- [ ] PUT /users/profile updates name, language, timezone
- [ ] PUT /users/password changes password after verifying current
- [ ] GET /users/stats returns aggregated trading metrics
- [ ] DELETE /users/account soft-deletes user and anonymizes data
- [ ] All endpoints require authentication
- [ ] Tests pass with >= 80% coverage
