"""Alerts router — 5 endpoints for rules CRUD + paginated history."""

import redis.asyncio as redis
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db, get_redis
from app.modules.alerts.schemas import PaginatedHistory, RuleCreate, RuleResponse, RuleUpdate
from app.modules.alerts.service import AlertsService
from app.modules.auth.models import User
from app.shared.responses import success_response

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/rules")
async def list_rules(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """List all alert rules for the current user."""
    service = AlertsService(db, redis_client)
    rules = await service.list_rules(str(current_user.id))

    data = [RuleResponse.model_validate(r).model_dump() for r in rules]
    return success_response(data)


@router.post("/rules")
async def create_rule(
    body: RuleCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Create a new alert rule (free plan: max 3 active rules)."""
    service = AlertsService(db, redis_client)
    rule = await service.create_rule(str(current_user.id), body)

    return success_response(RuleResponse.model_validate(rule).model_dump())


@router.put("/rules/{rule_id}")
async def update_rule(
    rule_id: str,
    body: RuleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Update threshold or is_active for an alert rule."""
    service = AlertsService(db, redis_client)
    rule = await service.update_rule(rule_id, str(current_user.id), body)

    return success_response(RuleResponse.model_validate(rule).model_dump())


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Delete an alert rule."""
    service = AlertsService(db, redis_client)
    await service.delete_rule(rule_id, str(current_user.id))

    return success_response(None, message="Alert rule deleted")


@router.get("/history")
async def get_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    rule_id: str | None = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Get paginated alert history with optional rule_id filter."""
    service = AlertsService(db, redis_client)
    items, total = await service.get_history(
        user_id=str(current_user.id),
        page=page,
        limit=limit,
        rule_id=rule_id,
    )

    pages = -(-total // limit) if limit > 0 else 0  # ceil division

    data = PaginatedHistory(
        items=[{
            "id": str(h.id),
            "user_id": str(h.user_id),
            "rule_id": str(h.rule_id),
            "upload_id": str(h.upload_id) if h.upload_id else None,
            "triggered_value": h.triggered_value,
            "triggered_at": h.triggered_at,
        } for h in items],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )

    return success_response(data.model_dump())
