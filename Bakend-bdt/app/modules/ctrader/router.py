"""cTrader router with 5 endpoints."""

import redis.asyncio as redis
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db, get_redis
from app.modules.auth.models import User
from app.modules.ctrader.schemas import (
    CredentialsCreate,
    CredentialsResponse,
    SyncRequest,
    SyncResponse,
    TestResponse,
)
from app.modules.ctrader.service import CtraderService

router = APIRouter(prefix="/ctrader", tags=["ctrader"])


@router.post("/credentials", response_model=CredentialsResponse)
async def store_credentials(
    data: CredentialsCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Store cTrader credentials (encrypted at rest)."""
    service = CtraderService(db, redis_client)
    result = await service.store_credentials(
        str(current_user.id),
        data.model_dump(),
    )
    return result


@router.get("/test", response_model=TestResponse)
async def test_connection(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Test cTrader connection with stored credentials."""
    service = CtraderService(db, redis_client)
    result = await service.test_connection(str(current_user.id))
    return result


@router.post("/sync", response_model=SyncResponse)
async def sync_trades(
    data: SyncRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Start trade sync from cTrader."""
    service = CtraderService(db, redis_client)
    result = await service.sync_trades(
        str(current_user.id),
        data.mode,
        data.date,
    )
    return {
        "job_id": result["upload_id"],
        "status": result["status"],
        "estimated_trades": result["total_trades"],
    }


@router.delete("/credentials", status_code=204)
async def delete_credentials(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Delete cTrader credentials."""
    service = CtraderService(db, redis_client)
    await service.delete_credentials(str(current_user.id))
