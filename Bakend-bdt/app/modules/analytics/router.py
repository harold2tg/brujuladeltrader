"""Analytics router with 14 endpoints."""

import redis.asyncio as redis
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db, get_redis
from app.modules.analytics.service import AnalyticsService
from app.modules.auth.models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/compare")
async def compare_data_sources(
    ids: str = Query(..., description="Comma-separated data source IDs"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Compare two data sources side-by-side with deltas."""
    if not ids:
        from app.shared.exceptions import BadRequestException
        raise BadRequestException("Missing required query parameter: ids")

    id_list = [i.strip() for i in ids.split(",")]
    if len(id_list) != 2:
        from app.shared.exceptions import BadRequestException
        raise BadRequestException("Exactly two data source IDs required")

    if id_list[0] == id_list[1]:
        from app.shared.exceptions import BadRequestException
        raise BadRequestException("Data source IDs must be different")

    service = AnalyticsService(db, redis_client)
    result = await service.compare_data_sources(
        id_list[0], id_list[1], str(current_user.id)
    )

    return {"success": True, "data": result}


@router.get("/{data_source_id}")
async def get_full_metrics(
    data_source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Get full metrics with all dimensions."""
    service = AnalyticsService(db, redis_client)
    result = await service.get_full_metrics(data_source_id, str(current_user.id))

    return {"success": True, "data": result}


@router.get("/{data_source_id}/summary")
async def get_summary(
    data_source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Get global metrics only."""
    service = AnalyticsService(db, redis_client)
    result = await service.get_summary(data_source_id, str(current_user.id))

    return {"success": True, "data": result}


@router.get("/{data_source_id}/by-hour")
async def get_by_hour(
    data_source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Get hourly breakdown."""
    service = AnalyticsService(db, redis_client)
    result = await service.get_by_hour(data_source_id, str(current_user.id))

    return {"success": True, "data": result}


@router.get("/{data_source_id}/by-day")
async def get_by_day(
    data_source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Get day of week breakdown."""
    service = AnalyticsService(db, redis_client)
    result = await service.get_by_day(data_source_id, str(current_user.id))

    return {"success": True, "data": result}


@router.get("/{data_source_id}/by-month")
async def get_by_month(
    data_source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Get monthly breakdown."""
    service = AnalyticsService(db, redis_client)
    result = await service.get_by_month(data_source_id, str(current_user.id))

    return {"success": True, "data": result}


@router.get("/{data_source_id}/by-week")
async def get_by_week(
    data_source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Get weekly breakdown."""
    service = AnalyticsService(db, redis_client)
    result = await service.get_by_week(data_source_id, str(current_user.id))

    return {"success": True, "data": result}


@router.get("/{data_source_id}/by-semester")
async def get_by_semester(
    data_source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Get semester breakdown."""
    service = AnalyticsService(db, redis_client)
    result = await service.get_by_semester(data_source_id, str(current_user.id))

    return {"success": True, "data": result}


@router.get("/{data_source_id}/by-year")
async def get_by_year(
    data_source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Get yearly breakdown."""
    service = AnalyticsService(db, redis_client)
    result = await service.get_by_year(data_source_id, str(current_user.id))

    return {"success": True, "data": result}


@router.get("/{data_source_id}/by-session")
async def get_by_session(
    data_source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Get session breakdown."""
    service = AnalyticsService(db, redis_client)
    result = await service.get_by_session(data_source_id, str(current_user.id))

    return {"success": True, "data": result}


@router.get("/{data_source_id}/streaks")
async def get_streaks(
    data_source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Get streak data."""
    service = AnalyticsService(db, redis_client)
    result = await service.get_streaks(data_source_id, str(current_user.id))

    return {"success": True, "data": result}


@router.get("/{data_source_id}/distribution")
async def get_distribution(
    data_source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Get distribution buckets."""
    service = AnalyticsService(db, redis_client)
    result = await service.get_distribution(data_source_id, str(current_user.id))

    return {"success": True, "data": result}


@router.get("/{data_source_id}/simulate")
async def get_simulations(
    data_source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Get simulation results."""
    service = AnalyticsService(db, redis_client)
    result = await service.get_simulations(data_source_id, str(current_user.id))

    return {"success": True, "data": result}


@router.get("/{data_source_id}/equity-curve")
async def get_equity_curve(
    data_source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Get equity curve (balance per trade)."""
    service = AnalyticsService(db, redis_client)
    result = await service.get_equity_curve(data_source_id, str(current_user.id))

    return {"success": True, "data": result}
