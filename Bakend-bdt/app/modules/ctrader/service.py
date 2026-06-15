"""cTrader service for credential management and trade sync."""

import logging
import uuid
from datetime import datetime, timezone

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.ctrader.client import CtraderClient, health_check
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
        """Store encrypted cTrader credentials and auto-discover account ID."""
        # Check if credentials already exist
        result = await self.db.execute(
            select(CtraderCredentials).where(CtraderCredentials.user_id == uuid.UUID(user_id))
        )
        existing = result.scalar_one_or_none()

        # Determine host based on is_demo flag
        is_demo = data.get("is_demo", False)
        host = settings.CTRADER_HOST_DEMO if is_demo else settings.CTRADER_HOST_LIVE

        # Save credentials first (account_id might be overwritten by auto-discovery)
        account_id_to_store = data["account_id"]

        if existing:
            existing.client_id_enc = encrypt(data["client_id"])
            existing.client_secret_enc = encrypt(data["client_secret"])
            existing.access_token_enc = encrypt(data["access_token"])
            existing.account_id_enc = encrypt(account_id_to_store)
            existing.is_demo = is_demo
            existing.updated_at = datetime.now(timezone.utc)
        else:
            creds = CtraderCredentials(
                user_id=uuid.UUID(user_id),
                client_id_enc=encrypt(data["client_id"]),
                client_secret_enc=encrypt(data["client_secret"]),
                access_token_enc=encrypt(data["access_token"]),
                account_id_enc=encrypt(account_id_to_store),
                is_demo=is_demo,
            )
            self.db.add(creds)

        await self.db.commit()

        # Test connection with real cTrader API
        client = CtraderClient(host, settings.CTRADER_PORT, is_demo=is_demo)
        connected = await client.connect()

        account_name = None
        broker_name = None
        discovered_account_id = None

        if connected:
            client_id = data["client_id"]
            client_secret = data["client_secret"]
            access_token = data["access_token"]

            # Authenticate app
            app_auth = await client.authenticate_app(client_id, client_secret)
            if app_auth:
                # Auto-discover accounts using access token
                accounts = await client.get_accounts(access_token)
                if accounts:
                    # Use the first account (or match by provided account_id if numeric)
                    provided_id = account_id_to_store.strip()
                    matched = None
                    if provided_id.isdigit():
                        # Try to match the provided numeric ID
                        matched = next(
                            (a for a in accounts if a["account_id"] == provided_id), None
                        )
                    if not matched:
                        # Use first available account
                        matched = accounts[0]

                    discovered_account_id = matched["account_id"]
                    account_name = matched.get("account_name", "cTrader Account")
                    broker_name = matched.get("broker_name", "Broker")
                    is_live = matched.get("is_live", False)

                    logger.info(
                        "Discovered account: id=%s, name=%s, broker=%s, live=%s",
                        discovered_account_id, account_name, broker_name, is_live,
                    )

                    # Update stored account_id with the discovered numeric ID
                    target = existing if existing else creds
                    target.account_id_enc = encrypt(discovered_account_id)
                    target.account_name = account_name
                    target.broker_name = broker_name
                    target.is_demo = not is_live
                    await self.db.commit()
                else:
                    logger.warning("No accounts found for this access token")

            await client.disconnect()

        return {
            "connected": connected and discovered_account_id is not None,
            "account_name": account_name,
            "broker": broker_name,
            "account_id": discovered_account_id,
        }

    async def test_connection(self, user_id: str) -> dict:
        """Test cTrader connection with stored credentials."""
        result = await self.db.execute(
            select(CtraderCredentials).where(CtraderCredentials.user_id == uuid.UUID(user_id))
        )
        creds = result.scalar_one_or_none()

        if not creds:
            raise NotFoundException("cTrader credentials not configured")

        host = settings.CTRADER_HOST_DEMO if creds.is_demo else settings.CTRADER_HOST_LIVE
        connected, latency_ms = await health_check(host, settings.CTRADER_PORT)

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
        host = settings.CTRADER_HOST_DEMO if creds.is_demo else settings.CTRADER_HOST_LIVE
        client = CtraderClient(host, settings.CTRADER_PORT, is_demo=creds.is_demo)
        await client.connect()

        client_id = decrypt(creds.client_id_enc)
        client_secret = decrypt(creds.client_secret_enc)
        access_token = decrypt(creds.access_token_enc)
        account_id = decrypt(creds.account_id_enc)

        # Authenticate app
        app_auth = await client.authenticate_app(client_id, client_secret)
        if not app_auth:
            await client.disconnect()
            raise BadRequestException("Failed to authenticate cTrader application")

        # Auto-discover account ID if stored value is not numeric
        if not account_id.strip().isdigit():
            accounts = await client.get_accounts(access_token)
            if accounts:
                matched = accounts[0]  # Use first available
                account_id = matched["account_id"]
                # Update stored account_id
                creds.account_id_enc = encrypt(account_id)
                await self.db.commit()
                logger.info("Auto-discovered account_id: %s", account_id)
            else:
                await client.disconnect()
                raise BadRequestException("No cTrader accounts found for this access token")

        # Authenticate account
        acc_auth = await client.authenticate_account(access_token, account_id)
        if not acc_auth:
            await client.disconnect()
            raise BadRequestException("Failed to authenticate cTrader account. Check your access token.")

        # Get symbol list to map symbolId -> symbol name
        symbols = await client.get_symbols(account_id)
        logger.info("Loaded %d symbols from cTrader", len(symbols))

        from_timestamp_ms = int(from_date.timestamp() * 1000)
        to_timestamp_ms = int(to_date.timestamp() * 1000)

        deals = await client.get_deals_history(
            access_token, account_id, from_timestamp_ms, to_timestamp_ms
        )

        await client.disconnect()

        # Process deals — only keep CLOSE deals (those with closePositionDetail)
        # Opening deals have no closePositionDetail, entry_price=0, net_pnl=0
        trades = []
        skipped_opens = 0
        for idx, deal in enumerate(deals):
            # Skip opening deals — they have no closePositionDetail
            if not deal.get("isClose", False):
                skipped_opens += 1
                continue

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

            # Map symbolId to symbol name
            symbol_id = deal.get("symbolId", 0)
            symbol_name = symbols.get(symbol_id, f"SYM_{symbol_id}")

            # Map trade side: 1=BUY, 2=SELL
            trade_side = deal.get("tradeSide", 1)
            direction = "Buy" if trade_side == 1 else "Sell"

            # Get prices from closePositionDetail
            entry_price = deal.get("entryPrice", 0)
            close_price = deal.get("executionPrice", 0)

            # Get PnL from closePositionDetail (in cents, divide by 100)
            gross_profit = deal.get("grossProfit", 0)
            commission = deal.get("commissionDetail", 0)
            swap = deal.get("swap", 0)

            # moneyDigits: 2 means values are in cents (divide by 100)
            money_digits = deal.get("moneyDigits", 2)
            divisor = 10 ** money_digits

            net_pnl = gross_profit / divisor if gross_profit else 0
            commission_usd = commission / divisor if commission else 0
            swap_usd = swap / divisor if swap else 0

            # Volume (already divided by 100 in client)
            volume = deal.get("volume", 0) / 100

            # Timestamps
            execution_ts = deal.get("executionTimestamp", 0)
            closed_at = datetime.fromtimestamp(execution_ts / 1000, tz=timezone.utc) if execution_ts else datetime.now(timezone.utc)

            # Balance from closePositionDetail
            balance_raw = deal.get("balance", 0)
            balance = balance_raw / divisor if balance_raw else 0

            # Map deal to trade
            trade_data = {
                "upload_id": upload.id,
                "user_id": uuid.UUID(user_id),
                "symbol": symbol_name,
                "direction": direction,
                "closed_at": closed_at,
                "entry_price": entry_price,
                "close_price": close_price,
                "lot_size": volume,
                "net_pnl": net_pnl,
                "balance": balance,
                "deal_id": deal_id,
            }

            # Calculate derived fields
            trade_data = calculate_derived_fields(trade_data, idx + 1)

            trade = Trade(**trade_data)
            trades.append(trade)

        logger.info(
            "Processed %d deals: %d close trades, %d opening deals skipped",
            len(deals), len(trades), skipped_opens,
        )

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
