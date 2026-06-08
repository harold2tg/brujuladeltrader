"""User profile router."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.modules.users.schemas import (
    AccountDelete,
    PasswordChange,
    UserStats,
    UserProfileUpdate,
)
from app.modules.users.service import UserService
from app.shared.responses import success_response

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency that provides a UserService instance."""
    return UserService(db)


@router.get("/profile", response_model=dict)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user profile."""
    return success_response(
        data={
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.name,
            "plan": current_user.plan,
            "language": current_user.language,
            "timezone": current_user.timezone,
            "created_at": current_user.created_at.isoformat(),
            "is_active": current_user.is_active,
        }
    )


@router.put("/profile", response_model=dict)
async def update_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """Update user profile."""
    updated = await user_service.update_profile(str(current_user.id), data)
    return success_response(
        data={
            "id": str(updated.id),
            "email": updated.email,
            "name": updated.name,
            "plan": updated.plan,
            "language": updated.language,
            "timezone": updated.timezone,
            "created_at": updated.created_at.isoformat(),
            "is_active": updated.is_active,
        },
        message="Profile updated successfully",
    )


@router.put("/password", response_model=dict)
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """Change user password."""
    await user_service.change_password(str(current_user.id), data)
    return success_response(data={}, message="Password changed successfully")


@router.get("/stats", response_model=dict)
async def get_stats(
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """Get aggregated user statistics."""
    stats = await user_service.get_stats(str(current_user.id))
    return success_response(data=stats)


@router.delete("/account", response_model=dict)
async def delete_account(
    data: AccountDelete,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """Delete user account (soft delete with anonymization)."""
    await user_service.delete_account(str(current_user.id), data.password)
    return success_response(data={}, message="Account deleted successfully")
