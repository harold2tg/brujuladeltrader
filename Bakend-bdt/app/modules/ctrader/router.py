"""cTrader router with OAuth2 flow."""

import secrets
import urllib.parse

import httpx
import redis.asyncio as redis
from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_active_user, get_db, get_redis
from app.modules.auth.models import User
from app.modules.ctrader.schemas import (
    AuthorizeRequest,
    CredentialsCreate,
    CredentialsResponse,
    SyncRequest,
    SyncResponse,
    TestResponse,
)
from app.modules.ctrader.service import CtraderService

router = APIRouter(prefix="/ctrader", tags=["ctrader"])

CTRADER_AUTH_URL = "https://openapi.ctrader.com/apps/authorize"
CTRADER_TOKEN_URL = "https://openapi.ctrader.com/apps/token"


@router.post("/authorize")
async def authorize_ctrader(
    data: AuthorizeRequest,
    current_user: User = Depends(get_current_active_user),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Start OAuth2 flow: store client credentials and return the authorization URL."""
    # Generate state token to prevent CSRF
    state = secrets.token_urlsafe(32)

    # Store client_id, client_secret, is_demo and user_id in Redis (5 min TTL)
    await redis_client.setex(
        f"ctrader_oauth:{state}",
        300,
        f"{data.client_id}|{data.client_secret}|{str(current_user.id)}|{'1' if data.is_demo else '0'}",
    )

    # Build the authorization URL
    redirect_uri = f"{settings.CTRADER_REDIRECT_URI}"
    params = {
        "client_id": data.client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "trading",
        "state": state,
    }
    auth_url = f"{CTRADER_AUTH_URL}?{urllib.parse.urlencode(params)}"

    return {"auth_url": auth_url, "state": state}


@router.get("/callback")
async def ctrader_callback(
    code: str = Query(...),
    state: str = Query(...),
    redis_client: redis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    """OAuth2 callback: exchange code for access token and store credentials."""
    # Retrieve stored data from Redis
    stored = await redis_client.get(f"ctrader_oauth:{state}")
    if not stored:
        return RedirectResponse(
            url="http://localhost:3001/es/ctrader?error=expired",
            status_code=302,
        )

    # Parse stored data
    parts = stored.decode().split("|")
    client_id = parts[0]
    client_secret = parts[1]
    user_id = parts[2]
    is_demo = parts[3] == "1"

    # Clean up Redis
    await redis_client.delete(f"ctrader_oauth:{state}")

    # Exchange authorization code for access token
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                CTRADER_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": settings.CTRADER_REDIRECT_URI,
                },
                timeout=30,
            )
            token_data = token_response.json()
    except Exception as e:
        return RedirectResponse(
            url=f"http://localhost:3001/es/ctrader?error=token_exchange_failed",
            status_code=302,
        )

    if "access_token" not in token_data:
        return RedirectResponse(
            url=f"http://localhost:3001/es/ctrader?error=no_access_token",
            status_code=302,
        )

    access_token = token_data["access_token"]

    # Now discover accounts using the access token
    from app.modules.ctrader.client import CtraderClient

    host = settings.CTRADER_HOST_DEMO if is_demo else settings.CTRADER_HOST_LIVE
    ctrader_client = CtraderClient(host, settings.CTRADER_PORT, is_demo=is_demo)
    await ctrader_client.connect()

    account_id = None
    account_name = None
    broker_name = None

    app_auth = await ctrader_client.authenticate_app(client_id, client_secret)
    if app_auth:
        accounts = await ctrader_client.get_accounts(access_token)
        if accounts:
            matched = accounts[0]
            account_id = matched["account_id"]
            account_name = matched.get("account_name", "cTrader Account")
            broker_name = matched.get("broker_name", "Broker")

    await ctrader_client.disconnect()

    if not account_id:
        return RedirectResponse(
            url="http://localhost:3001/es/ctrader?error=no_accounts",
            status_code=302,
        )

    # Store credentials in database
    service = CtraderService(db, redis_client)
    await service.store_credentials_oauth(
        user_id=user_id,
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
        account_id=account_id,
        account_name=account_name,
        broker_name=broker_name,
        is_demo=is_demo,
    )

    # Redirect back to frontend with success
    return RedirectResponse(
        url="http://localhost:3001/es/ctrader?connected=true",
        status_code=302,
    )


@router.get("/credentials")
async def get_credentials(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's cTrader credentials (masked)."""
    from sqlalchemy import select
    from app.modules.ctrader.models import CtraderCredentials

    result = await db.execute(
        select(CtraderCredentials).where(
            CtraderCredentials.user_id == current_user.id
        )
    )
    creds = result.scalar_one_or_none()

    if not creds:
        return {"data": None}

    return {
        "data": {
            "id": str(creds.id),
            "account_name": creds.account_name,
            "broker_name": creds.broker_name,
            "is_demo": creds.is_demo,
            "has_credentials": True,
        }
    }


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
        "job_id": result["data_source_id"],
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
