"""cTrader router with OAuth2 flow."""

import logging
import secrets
import urllib.parse

import redis.asyncio as redis
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_active_user, get_db, get_redis
from app.modules.auth.models import User
from app.modules.ctrader.schemas import (
    AuthorizeRequest,
    AuthResponse,
    CredentialsCreate,
    CredentialsResponse,
    SyncRequest,
    SyncResponse,
    TestResponse,
)
from app.modules.ctrader.service import CtraderService

router = APIRouter(prefix="/ctrader", tags=["ctrader"])
logger = logging.getLogger(__name__)

CTRADER_AUTH_URL = "https://openapi.ctrader.com/apps/authorize"
FRONTEND_URL = "http://localhost:3001"


def _callback_html(success: bool, error: str = "") -> str:
    """Return HTML that closes the popup and notifies the parent window."""
    status = "success" if success else "error"
    return f"""<!DOCTYPE html>
<html>
<head><title>cTrader Connection</title></head>
<body>
<script>
  if (window.opener) {{
    window.opener.postMessage(
      {{ type: 'ctrader-oauth', status: '{status}', error: '{error}' }},
      '{FRONTEND_URL}'
    );
  }}
  window.close();
</script>
<p>Connection {("completed" if success else "failed")}. You can close this window.</p>
</body>
</html>"""


@router.get("/auth", response_model=AuthResponse)
async def get_auth_url(
    current_user: User = Depends(get_current_active_user),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Generate OAuth authorization URL using server-side credentials.

    The user just clicks "Connect cTrader" — no manual credential entry needed.
    Client ID and Secret come from server config (CTRADER_CLIENT_ID / CTRADER_CLIENT_SECRET).
    """
    if not settings.CTRADER_CLIENT_ID or not settings.CTRADER_CLIENT_SECRET:
        from app.shared.exceptions import BadRequestException
        raise BadRequestException(
            "cTrader OAuth is not configured. Set CTRADER_CLIENT_ID and CTRADER_CLIENT_SECRET."
        )

    # Generate state token to prevent CSRF
    state = secrets.token_urlsafe(32)

    # Store user_id, is_demo in Redis (5 min TTL) — client creds come from server config
    await redis_client.setex(
        f"ctrader_oauth:{state}",
        300,
        f"{settings.CTRADER_CLIENT_ID}|{settings.CTRADER_CLIENT_SECRET}|{str(current_user.id)}|1",
    )

    # Build the authorization URL
    params = {
        "client_id": settings.CTRADER_CLIENT_ID,
        "redirect_uri": settings.CTRADER_REDIRECT_URI,
        "response_type": "code",
        "scope": "trading",
        "state": state,
    }
    auth_url = f"{CTRADER_AUTH_URL}?{urllib.parse.urlencode(params)}"

    return {"auth_url": auth_url, "state": state}


@router.post("/authorize")
async def authorize_ctrader(
    data: AuthorizeRequest,
    current_user: User = Depends(get_current_active_user),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Start OAuth2 flow with user-provided client credentials (legacy).

    Prefer GET /ctrader/auth for the one-click flow.
    """
    # Generate state token to prevent CSRF
    state = secrets.token_urlsafe(32)

    # Store client_id, client_secret, is_demo and user_id in Redis (5 min TTL)
    await redis_client.setex(
        f"ctrader_oauth:{state}",
        300,
        f"{data.client_id}|{data.client_secret}|{str(current_user.id)}|{'1' if data.is_demo else '0'}",
    )

    # Build the authorization URL
    params = {
        "client_id": data.client_id,
        "redirect_uri": settings.CTRADER_REDIRECT_URI,
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
    """OAuth2 callback: exchange code for tokens, store credentials, close popup."""
    # Retrieve stored data from Redis
    stored = await redis_client.get(f"ctrader_oauth:{state}")
    if not stored:
        return HTMLResponse(
            _callback_html(False, "expired"),
            status_code=200,
        )

    # Parse stored data
    parts = stored.decode().split("|")
    client_id = parts[0]
    client_secret = parts[1]
    user_id = parts[2]
    is_demo = parts[3] == "1"

    # Clean up Redis
    await redis_client.delete(f"ctrader_oauth:{state}")

    # Exchange authorization code for access token + refresh token
    from app.modules.ctrader.client import exchange_code_for_token

    try:
        token_data = await exchange_code_for_token(
            code=code,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=settings.CTRADER_REDIRECT_URI,
        )
    except Exception as e:
        logger.error("Token exchange failed: %s", e)
        return HTMLResponse(
            _callback_html(False, "token_exchange_failed"),
            status_code=200,
        )

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    if not access_token:
        return HTMLResponse(
            _callback_html(False, "no_access_token"),
            status_code=200,
        )

    # Discover accounts using the access token
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
        return HTMLResponse(
            _callback_html(False, "no_accounts"),
            status_code=200,
        )

    # Store credentials in database
    service = CtraderService(db, redis_client)
    await service.store_credentials_oauth(
        user_id=user_id,
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
        refresh_token=refresh_token,
        account_id=account_id,
        account_name=account_name,
        broker_name=broker_name,
        is_demo=is_demo,
    )

    # Return HTML that closes popup and notifies parent
    return HTMLResponse(
        _callback_html(True),
        status_code=200,
    )


@router.post("/refresh")
async def refresh_token(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Refresh the access_token using the stored refresh_token."""
    service = CtraderService(db, redis_client)
    result = await service.refresh_token(str(current_user.id))
    return {"success": True, "data": result}


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
