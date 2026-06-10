"""cTrader service for credential management and trade sync."""

import logging
import uuid
from datetime import datetime, timezone

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.ctrader.client import CtraderClient
from app.modules.ctrader.models import CtraderCredentials
from app.modules.parser.models import Trade
from app.modules.parser.service import calculate_derived_fields, classify_session
from app.modules.uploads.models import Upload
from app.shared.crypto import decrypt, encrypt, mask_token
from app.shared.exceptions import BadRequestException, NotFoundException

logger = logging.getLogger(__name__)


class CtraderService:
    """cTrader service for credential management and trade sync."""

    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client

    async def store_credentials(self, user_id: str, data: dict) -> dict:
        """Store encrypted cTrader credentials."""
        # Check if credentials already exist
        result = await self.db.execute(
            select(CtraderCredentials).where(CtraderCredentials.user_id == uuid.UUID(user_id))
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.client_id_enc = encrypt(data["client_id"])
            existing.client_secret_enc = encrypt(data["client_secret"])
            existing.access_token_enc = encrypt(data["access_token"])
            existing.account_id_enc = encrypt(data["account_id"])
            existing.updated_at = datetime.now(timezone.utc)
        else:
            # Create new
            creds = CtraderCredentials(
                user_id=uuid.UUID(user_id),
                client_id_enc=encrypt(data["client_id"]),
                client_secret_enc=encrypt(data["client_secret"]),
                access_token_enc=encrypt(data["access_token"]),
                account_id_enc=encrypt(data["account_id"]),
            )
            self.db.add(creds)

        await self.db.commit()

        # Test connection
        client = CtraderClient(settings.CTRADER_HOST_DEMO, settings.CTRADER_PORT, is_demo=True)
        connected = await client.connect()

        account_name = None
        broker_name = None
        if connected:
            access_token = decrypt(existing.access_token_enc if existing else creds.access_token_enc)
            account_info = await client.get_account_info(access_token)
            if account_info:
                account_name = account_info.get("account_name")
                broker_name = account_info.get("broker_name")
                # Update with account info
                if existing:
                    existing.account_name = account_name
                    existing.broker_name = broker_name
                    await self.db.commit()

        return {
            "connected": connected,
            "account_name": account_name,
            "broker": broker_name,
        }

    async def test_connection(self, user_id: str) -> dict:
        """Test cTrader connection with stored credentials."""
        result = await self.db.execute(
            select(CtraderCredentials).where(CtraderCredentials.user_id == uuid.UUID(user_id))
        )
        creds = result.scalar_one_or_none()

        if not creds:
            raise NotFoundException("cTrader credentials not configured")

        client = CtraderClient(settings.CTRADER_HOST_DEMO, settings.CTRADER_PORT, is_demo=creds.is_demo)
        connected, latency_ms = await client.health_check()

        if not connected:
            return {
                "connected": False,
                "latency_ms": latency_ms,
                "error": "Failed to connect to cTrader API",
            }

        return {
            "connected": True,
            "latency_ms": latency_ms,
        }

    async def sync_trades(self, user_id: str, mode: str, date_str: str) -> dict:
        """Start trade sync from cTrader."""
        # Get credentials
        result = await self.db.execute(
            select(CtraderCredentials).where(CtraderCredentials.user_id == uuid.UUID(user_id))
        )
        creds = result.scalar_one_or_none()

        if not creds:
            raise NotFoundException("cTrader credentials not configured")

        # Calculate date range
        date = datetime.strptime(date_str, "%Y-%m-%d")
        if mode == "day":
            from_date = date.replace(hour=0, minute=0, second=0)
            to_date = date.replace(hour=23, minute=59, second=59)
        elif mode == "month":
            from_date = date.replace(day=1, hour=0, minute=0, second=0)
            if date.month == 12:
                to_date = date.replace(year=date.year + 1, month=1, day=1)
            else:
                to_date = date.replace(month=date.month + 1, day=1)
        elif mode == "year":
            from_date = date.replace(month=1, day=1, hour=0, minute=0, second=0)
            to_date = date.replace(year=date.year + 1, month=1, day=1)
        else:
            raise BadRequestException("Invalid mode. Use 'day', 'month', or 'year'")

        # Create upload record
        upload = Upload(
            user_id=uuid.UUID(user_id),
            original_name=f"cTrader_{mode}_{date_str}",
            stored_name=f"ctrader_{uuid.uuid4()}.sync",
            stored_path="",
            file_size_kb=0,
            status="processing",
            source="ctrader",
            period_label=date_str,
        )
        self.db.add(upload)
        await self.db.commit()

        # Get deals from cTrader
        client = CtraderClient(settings.CTRADER_HOST_DEMO, settings.CTRADER_PORT, is_demo=creds.is_demo)
        await client.connect()

        access_token = decrypt(creds.access_token_enc)
        account_id = decrypt(creds.account_id_enc)

        from_timestamp_ms = int(from_date.timestamp() * 1000)
        to_timestamp_ms = int(to_date.timestamp() * 1000)

        deals = await client.get_deals_history(
            access_token, account_id, from_timestamp_ms, to_timestamp_ms
        )

        # Process deals
        trades = []
        for idx, deal in enumerate(deals):
            # Check for duplicate deal_id
            deal_id = str(deal.get("dealId", ""))
            if deal_id:
                existing_trade = await self.db.execute(
                    select(Trade).where(
                        Trade.user_id == uuid.UUID(user_id),
                        Trade.deal_id == deal_id,
                    )
                )
                if existing_trade.scalar_one_or_none():
                    continue  # Skip duplicate

            # Map deal to trade
            trade_data = {
                "upload_id": upload.id,
                "user_id": uuid.UUID(user_id),
                "symbol": deal.get("symbol", "XAUUSD"),
                "direction": "Buy" if deal.get("orderType") == 1 else "Sell",
                "closed_at": datetime.fromtimestamp(deal.get("executionTime", 0) / 1000, tz=timezone.utc),
                "entry_price": deal.get("openPrice", 0),
                "close_price": deal.get("closePrice", 0),
                "lot_size": deal.get("volume", 0),
                "net_pnl": deal.get("netProfit", 0),
                "balance": deal.get("balance", 0),
                "deal_id": deal_id,
            }

            # Calculate derived fields
            trade_data = calculate_derived_fields(trade_data, idx + 1)

            trade = Trade(**trade_data)
            trades.append(trade)

        # Insert trades
        if trades:
            self.db.add_all(trades)

        # Update upload
        upload.status = "ready"
        upload.total_trades = len(trades)
        if trades:
            dates = [t.closed_at for t in trades if t.closed_at]
            if dates:
                upload.date_from = min(dates).date()
                upload.date_to = max(dates).date()
        upload.processed_at = datetime.now(timezone.utc)

        await self.db.commit()

        return {
            "upload_id": str(upload.id),
            "status": "ready",
            "total_trades": len(trades),
        }

    async def delete_credentials(self, user_id: str) -> None:
        """Delete cTrader credentials."""
        result = await self.db.execute(
            select(CtraderCredentials).where(CtraderCredentials.user_id == uuid.UUID(user_id))
        )
        creds = result.scalar_one_or_none()

        if not creds:
            raise NotFoundException("cTrader credentials not configured")

        await self.db.delete(creds)
        await self.db.commit()
