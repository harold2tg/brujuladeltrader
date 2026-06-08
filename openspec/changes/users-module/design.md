# Design: users-module

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI App                             │
├─────────────────────────────────────────────────────────────┤
│  main.py (register users router)                            │
├─────────────────────────────────────────────────────────────┤
│  dependencies.py                                            │
│  ├── get_current_user(token) → User (from auth)             │
│  └── get_current_active_user(user) → User                   │
├─────────────────────────────────────────────────────────────┤
│  modules/users/                                             │
│  ├── router.py (endpoints)                                  │
│  ├── service.py (business logic)                            │
│  └── schemas.py (Pydantic models)                           │
├─────────────────────────────────────────────────────────────┤
│  modules/auth/                                              │
│  └── models.py (User model - reused)                        │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │
│  (users table)  │
└─────────────────┘
```

## File Structure

```
app/modules/users/
├── __init__.py
├── router.py
├── service.py
└── schemas.py
```

## Data Flow

### Get Profile Flow
```
Client → GET /users/profile (Header: Bearer <token>)
  │
  ├─→ Extract token from header
  ├─→ Decode JWT (verify signature + expiry)
  ├─→ Check jti not in Redis blacklist
  ├─→ Load user from DB
  └─→ Return user profile (without password_hash)
```

### Update Profile Flow
```
Client → PUT /users/profile (Header: Bearer <token>, Body: { name?, language?, timezone? })
  │
  ├─→ Authenticate user (same as get profile)
  ├─→ Validate input (Pydantic)
  ├─→ Update user fields
  ├─→ Save to DB
  └─→ Return updated user
```

### Change Password Flow
```
Client → PUT /users/password (Header: Bearer <token>, Body: { current_password, new_password })
  │
  ├─→ Authenticate user
  ├─→ Verify current_password against stored hash
  ├─→ If wrong → return 401
  ├─→ Validate new_password strength
  ├─→ Hash new_password with bcrypt
  ├─→ Update password_hash in DB
  └─→ Return success message
```

### Get Stats Flow
```
Client → GET /users/stats (Header: Bearer <token>)
  │
  ├─→ Authenticate user
  ├─→ Query aggregates from uploads + trades tables
  │   ├── total_uploads (COUNT uploads WHERE user_id = ?)
  │   ├── total_trades (COUNT trades WHERE user_id = ?)
  │   ├── total_pnl (SUM net_pnl FROM trades WHERE user_id = ?)
  │   ├── win_rate (COUNT is_winner / total_trades)
  │   ├── avg_rr_ratio (AVG win / AVG loss)
  │   ├── best_month (MAX monthly_pnl)
  │   └── worst_month (MIN monthly_pnl)
  ├─→ Optional: cache in Redis (TTL: 1 hour)
  └─→ Return stats
```

### Delete Account Flow
```
Client → DELETE /users/account (Header: Bearer <token>, Body: { password })
  │
  ├─→ Authenticate user
  ├─→ Verify password
  ├─→ If wrong → return 401
  ├─→ Anonymize user:
  │   ├── email = "deleted_{uuid}@deleted.local"
  │   ├── name = "Deleted User"
  │   └── is_active = False
  ├─→ Save to DB
  ├─→ Blacklist current token
  └─→ Return success message
```

## Key Implementation Details

### users/schemas.py
```python
from pydantic import BaseModel, field_validator
from typing import Optional
import pytz

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None

    @field_validator("language")
    @classmethod
    def validate_language(cls, v):
        if v and v not in ("es", "en"):
            raise ValueError("Language must be 'es' or 'en'")
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v):
        if v and v not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone: {v}")
        return v

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain lowercase")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain number")
        return v

class UserStats(BaseModel):
    total_uploads: int
    total_trades: int
    total_pnl: float
    win_rate: float
    avg_rr_ratio: Optional[float]
    best_month: Optional[float]
    worst_month: Optional[float]
```

### users/service.py
```python
class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, user_id: str) -> User:
        """Get user profile by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one()

    async def update_profile(self, user_id: str, data: UserProfileUpdate) -> User:
        """Update user profile."""
        user = await self.get_profile(user_id)
        if data.name is not None:
            user.name = data.name
        if data.language is not None:
            user.language = data.language
        if data.timezone is not None:
            user.timezone = data.timezone
        await self.db.commit()
        return user

    async def change_password(self, user_id: str, data: PasswordChange) -> None:
        """Change user password after verifying current."""
        user = await self.get_profile(user_id)
        if not verify_password(data.current_password, user.password_hash):
            raise UnauthorizedException("Current password is incorrect")
        user.password_hash = hash_password(data.new_password)
        await self.db.commit()

    async def get_stats(self, user_id: str) -> dict:
        """Get aggregated user statistics."""
        # SQL aggregates on uploads and trades tables
        ...

    async def delete_account(self, user_id: str, password: str) -> None:
        """Soft delete user and anonymize data."""
        user = await self.get_profile(user_id)
        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("Password is required to delete account")
        user.email = f"deleted_{user.id}@deleted.local"
        user.name = "Deleted User"
        user.is_active = False
        await self.db.commit()
```

### users/router.py
```python
router = APIRouter(prefix="/users", tags=["users"])

@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_active_user)):
    return success_response(data=UserResponse.model_validate(current_user))

@router.put("/profile")
async def update_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    updated = await user_service.update_profile(str(current_user.id), data)
    return success_response(data=UserResponse.model_validate(updated))

@router.put("/password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    await user_service.change_password(str(current_user.id), data)
    return success_response(message="Password changed successfully")

@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    stats = await user_service.get_stats(str(current_user.id))
    return success_response(data=stats)

@router.delete("/account")
async def delete_account(
    data: AccountDelete,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    await user_service.delete_account(str(current_user.id), data.password)
    return success_response(message="Account deleted successfully")
```

## Dependencies (pyproject.toml)

No new dependencies needed. Reuses:
- fastapi
- sqlalchemy
- bcrypt (from auth module)
- pydantic

## Testing Strategy

- Unit tests for service layer (mock DB)
- Integration tests for endpoints (httpx AsyncClient)
- Test cases:
  - Get profile success
  - Update profile success + validation errors
  - Change password success + wrong current password
  - Get stats with data + no data
  - Delete account success + wrong password

## Security Considerations

1. **Password Verification**: Always verify current password before changes
2. **Soft Delete**: Never hard delete user data (analytics need history)
3. **Anonymization**: Email and name replaced, but trades kept for aggregate stats
4. **Token Blacklist**: Logout user after account deletion
5. **Input Validation**: Language and timezone validated against allowed values

## Rollback Plan

1. Delete users module files (router.py, service.py, schemas.py)
2. Remove users router registration from main.py
3. No database changes needed
