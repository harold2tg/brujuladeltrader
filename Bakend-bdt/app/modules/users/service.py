"""User profile service."""

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.auth.service import hash_password, verify_password
from app.modules.users.schemas import PasswordChange, UserProfileUpdate, UserStats
from app.shared.exceptions import UnauthorizedException


class UserService:
    """User profile management service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, user_id: str) -> User:
        """Get user profile by ID."""
        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise UnauthorizedException("User not found")
        return user

    async def update_profile(self, user_id: str, data: UserProfileUpdate) -> User:
        """Update user profile fields."""
        user = await self.get_profile(user_id)

        if data.name is not None:
            user.name = data.name
        if data.language is not None:
            user.language = data.language
        if data.timezone is not None:
            user.timezone = data.timezone

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, user_id: str, data: PasswordChange) -> None:
        """Change user password after verifying current password."""
        user = await self.get_profile(user_id)

        # Verify current password
        if not verify_password(data.current_password, user.password_hash):
            raise UnauthorizedException("Current password is incorrect")

        # Check new password is different
        if verify_password(data.new_password, user.password_hash):
            raise UnauthorizedException("New password must be different from current password")

        # Update password
        user.password_hash = hash_password(data.new_password)
        await self.db.commit()

    async def get_stats(self, user_id: str) -> dict:
        """Get aggregated user statistics from uploads and trades."""
        # Import models locally to avoid circular imports
        try:
            from app.modules.uploads.models import Upload
            from app.modules.parser.models import Trade
        except ImportError:
            # Modules not implemented yet - return empty stats
            return {
                "total_uploads": 0,
                "total_trades": 0,
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "avg_rr_ratio": None,
                "best_month": None,
                "worst_month": None,
            }

        user_uuid = uuid.UUID(user_id)

        # Total uploads
        uploads_result = await self.db.execute(
            select(func.count(Upload.id)).where(Upload.user_id == user_uuid)
        )
        total_uploads = uploads_result.scalar() or 0

        # Total trades
        trades_result = await self.db.execute(
            select(func.count(Trade.id)).where(Trade.user_id == user_uuid)
        )
        total_trades = trades_result.scalar() or 0

        if total_trades == 0:
            return {
                "total_uploads": total_uploads,
                "total_trades": 0,
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "avg_rr_ratio": None,
                "best_month": None,
                "worst_month": None,
            }

        # Total PnL
        pnl_result = await self.db.execute(
            select(func.sum(Trade.net_pnl)).where(Trade.user_id == user_uuid)
        )
        total_pnl = float(pnl_result.scalar() or 0)

        # Win rate
        winners_result = await self.db.execute(
            select(func.count(Trade.id)).where(
                Trade.user_id == user_uuid, Trade.is_winner == True
            )
        )
        winning_trades = winners_result.scalar() or 0
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

        # Average R:R ratio
        avg_win_result = await self.db.execute(
            select(func.avg(Trade.net_pnl)).where(
                Trade.user_id == user_uuid, Trade.is_winner == True
            )
        )
        avg_win = float(avg_win_result.scalar() or 0)

        avg_loss_result = await self.db.execute(
            select(func.avg(Trade.net_pnl)).where(
                Trade.user_id == user_uuid, Trade.is_winner == False
            )
        )
        avg_loss = float(avg_loss_result.scalar() or 0)

        avg_rr_ratio = avg_win / abs(avg_loss) if avg_loss != 0 else None

        # Monthly PnL for best/worst month
        monthly_result = await self.db.execute(
            select(
                Trade.month,
                Trade.year,
                func.sum(Trade.net_pnl).label("monthly_pnl")
            )
            .where(Trade.user_id == user_uuid)
            .group_by(Trade.year, Trade.month)
        )
        monthly_data = monthly_result.all()

        if monthly_data:
            monthly_pnls = [float(row.monthly_pnl) for row in monthly_data]
            best_month = max(monthly_pnls)
            worst_month = min(monthly_pnls)
        else:
            best_month = None
            worst_month = None

        return {
            "total_uploads": total_uploads,
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "avg_rr_ratio": avg_rr_ratio,
            "best_month": best_month,
            "worst_month": worst_month,
        }

    async def delete_account(self, user_id: str, password: str) -> None:
        """Soft delete user account and anonymize data."""
        user = await self.get_profile(user_id)

        # Verify password before deletion
        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("Password is required to delete account")

        # Anonymize user data
        user.email = f"deleted_{user.id}@deleted.local"
        user.name = "Deleted User"
        user.is_active = False

        await self.db.commit()
