"""Analytics service with Redis caching."""

import json
import logging
import uuid
from typing import Any, Callable

import pandas as pd
import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.analytics.metrics import (
    calculate_by_day,
    calculate_by_direction,
    calculate_by_hour,
    calculate_by_month,
    calculate_by_session,
    calculate_distribution,
    calculate_global_metrics,
    calculate_simulations,
    calculate_streaks,
)
from app.modules.parser.models import Trade
from app.modules.uploads.models import Upload
from app.shared.exceptions import NotFoundException

logger = logging.getLogger(__name__)

CACHE_TTL = 3600  # 1 hour


class AnalyticsService:
    """Analytics service for calculating trade metrics."""

    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client

    async def get_upload_or_404(self, upload_id: str, user_id: str) -> Upload:
        """Get upload and verify ownership. Raises 404 if not found or not owned."""
        result = await self.db.execute(
            select(Upload).where(Upload.id == uuid.UUID(upload_id))
        )
        upload = result.scalar_one_or_none()

        if not upload:
            raise NotFoundException("Upload not found")

        if str(upload.user_id) != user_id:
            raise NotFoundException("Upload not found")

        return upload

    def _cache_key(self, user_id: str, upload_id: str, endpoint: str) -> str:
        """Generate Redis cache key."""
        return f"analytics:{user_id}:{upload_id}:{endpoint}"

    async def get_cached(self, key: str) -> dict | None:
        """Get cached result from Redis."""
        try:
            cached = await self.redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            logger.warning("Redis cache read failed for key: %s", key)
        return None

    async def set_cached(self, key: str, data: dict) -> None:
        """Set cached result in Redis."""
        try:
            await self.redis.setex(key, CACHE_TTL, json.dumps(data))
        except Exception:
            logger.warning("Redis cache write failed for key: %s", key)

    async def _get_trades_df(self, upload_id: str) -> pd.DataFrame:
        """Get trades as a pandas DataFrame."""
        result = await self.db.execute(
            select(Trade).where(Trade.upload_id == uuid.UUID(upload_id))
        )
        trades = result.scalars().all()

        if not trades:
            return pd.DataFrame()

        data = [
            {
                "net_pnl": float(t.net_pnl),
                "hour_of_day": t.hour_of_day,
                "day_of_week": t.day_of_week,
                "month": t.month,
                "session": t.session,
                "direction": t.direction,
                "balance": float(t.balance) if t.balance else 0.0,
                "trade_number": t.trade_number,
            }
            for t in trades
        ]
        return pd.DataFrame(data)

    async def get_full_metrics(self, upload_id: str, user_id: str) -> dict:
        """Get full metrics with all dimensions."""
        cache_key = self._cache_key(user_id, upload_id, "full")
        cached = await self.get_cached(cache_key)
        if cached:
            return cached

        await self.get_upload_or_404(upload_id, user_id)
        df = await self._get_trades_df(upload_id)

        metrics = {
            "global": calculate_global_metrics(df),
            "by_hour": calculate_by_hour(df),
            "by_day": calculate_by_day(df),
            "by_month": calculate_by_month(df),
            "by_direction": calculate_by_direction(df),
            "by_session": calculate_by_session(df),
            "distribution": calculate_distribution(df),
            "streaks": calculate_streaks(df),
            "simulations": calculate_simulations(df),
        }

        await self.set_cached(cache_key, metrics)
        return metrics

    async def get_summary(self, upload_id: str, user_id: str) -> dict:
        """Get global metrics only."""
        cache_key = self._cache_key(user_id, upload_id, "summary")
        cached = await self.get_cached(cache_key)
        if cached:
            return cached

        await self.get_upload_or_404(upload_id, user_id)
        df = await self._get_trades_df(upload_id)
        metrics = calculate_global_metrics(df)

        await self.set_cached(cache_key, metrics)
        return metrics

    async def get_by_hour(self, upload_id: str, user_id: str) -> list[dict]:
        """Get hourly breakdown."""
        cache_key = self._cache_key(user_id, upload_id, "by-hour")
        cached = await self.get_cached(cache_key)
        if cached:
            return cached

        await self.get_upload_or_404(upload_id, user_id)
        df = await self._get_trades_df(upload_id)
        metrics = calculate_by_hour(df)

        await self.set_cached(cache_key, metrics)
        return metrics

    async def get_by_day(self, upload_id: str, user_id: str) -> list[dict]:
        """Get day of week breakdown."""
        cache_key = self._cache_key(user_id, upload_id, "by-day")
        cached = await self.get_cached(cache_key)
        if cached:
            return cached

        await self.get_upload_or_404(upload_id, user_id)
        df = await self._get_trades_df(upload_id)
        metrics = calculate_by_day(df)

        await self.set_cached(cache_key, metrics)
        return metrics

    async def get_by_month(self, upload_id: str, user_id: str) -> list[dict]:
        """Get monthly breakdown."""
        cache_key = self._cache_key(user_id, upload_id, "by-month")
        cached = await self.get_cached(cache_key)
        if cached:
            return cached

        await self.get_upload_or_404(upload_id, user_id)
        df = await self._get_trades_df(upload_id)
        metrics = calculate_by_month(df)

        await self.set_cached(cache_key, metrics)
        return metrics

    async def get_by_session(self, upload_id: str, user_id: str) -> list[dict]:
        """Get session breakdown."""
        cache_key = self._cache_key(user_id, upload_id, "by-session")
        cached = await self.get_cached(cache_key)
        if cached:
            return cached

        await self.get_upload_or_404(upload_id, user_id)
        df = await self._get_trades_df(upload_id)
        metrics = calculate_by_session(df)

        await self.set_cached(cache_key, metrics)
        return metrics

    async def get_streaks(self, upload_id: str, user_id: str) -> dict:
        """Get streak data."""
        cache_key = self._cache_key(user_id, upload_id, "streaks")
        cached = await self.get_cached(cache_key)
        if cached:
            return cached

        await self.get_upload_or_404(upload_id, user_id)
        df = await self._get_trades_df(upload_id)
        metrics = calculate_streaks(df)

        await self.set_cached(cache_key, metrics)
        return metrics

    async def get_distribution(self, upload_id: str, user_id: str) -> list[dict]:
        """Get distribution buckets."""
        cache_key = self._cache_key(user_id, upload_id, "distribution")
        cached = await self.get_cached(cache_key)
        if cached:
            return cached

        await self.get_upload_or_404(upload_id, user_id)
        df = await self._get_trades_df(upload_id)
        metrics = calculate_distribution(df)

        await self.set_cached(cache_key, metrics)
        return metrics

    async def get_simulations(self, upload_id: str, user_id: str) -> dict:
        """Get simulation results."""
        cache_key = self._cache_key(user_id, upload_id, "simulate")
        cached = await self.get_cached(cache_key)
        if cached:
            return cached

        await self.get_upload_or_404(upload_id, user_id)
        df = await self._get_trades_df(upload_id)
        metrics = calculate_simulations(df)

        await self.set_cached(cache_key, metrics)
        return metrics

    async def compare_uploads(self, upload_id_a: str, upload_id_b: str, user_id: str) -> dict:
        """Compare two uploads side-by-side with deltas."""
        cache_key = self._cache_key(user_id, f"{upload_id_a},{upload_id_b}", "compare")
        cached = await self.get_cached(cache_key)
        if cached:
            return cached

        await self.get_upload_or_404(upload_id_a, user_id)
        await self.get_upload_or_404(upload_id_b, user_id)

        df_a = await self._get_trades_df(upload_id_a)
        df_b = await self._get_trades_df(upload_id_b)

        metrics_a = calculate_global_metrics(df_a)
        metrics_b = calculate_global_metrics(df_b)

        # Calculate deltas
        delta = {}
        for key in metrics_a:
            val_a = metrics_a[key]
            val_b = metrics_b[key]
            if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                delta[key] = round(val_b - val_a, 2)
            else:
                delta[key] = None

        result = {
            "upload_a": {"upload_id": upload_id_a, "metrics": metrics_a},
            "upload_b": {"upload_id": upload_id_b, "metrics": metrics_b},
            "delta": delta,
        }

        await self.set_cached(cache_key, result)
        return result
