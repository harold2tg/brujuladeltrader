"""cTrader Open API client wrapper (Protobuf/TCP)."""

import asyncio
import logging
import time

logger = logging.getLogger(__name__)

# Rate limiting
LAST_REQUEST_TIME = 0.0
MIN_INTERVAL = 0.2  # 5 requests/second


async def _rate_limit():
    """Enforce rate limiting (5 req/s)."""
    global LAST_REQUEST_TIME
    now = time.time()
    elapsed = now - LAST_REQUEST_TIME
    if elapsed < MIN_INTERVAL:
        await asyncio.sleep(MIN_INTERVAL - elapsed)
    LAST_REQUEST_TIME = time.time()


class CtraderClient:
    """Wrapper for cTrader Open API (Protobuf/TCP)."""

    def __init__(self, host: str, port: int, is_demo: bool = False):
        self.host = host
        self.port = port
        self.is_demo = is_demo
        self._reader = None
        self._writer = None
        self._connected = False

    async def connect(self) -> bool:
        """Connect to cTrader API. Returns True if successful."""
        try:
            await _rate_limit()
            # In production, this would establish TCP connection
            # For now, return True for testing
            self._connected = True
            return True
        except Exception as e:
            logger.error("Failed to connect to cTrader: %s", e)
            return False

    async def disconnect(self):
        """Disconnect from cTrader API."""
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
        self._connected = False

    async def get_account_info(self, access_token: str) -> dict | None:
        """Get account information using access token."""
        if not self._connected:
            return None

        try:
            await _rate_limit()
            # In production, send ProtoOAGetAccountListByAccessTokenReq
            # For now, return mock data
            return {
                "account_name": "Demo Account",
                "broker_name": "Pepperstone",
            }
        except Exception as e:
            logger.error("Failed to get account info: %s", e)
            return None

    async def get_deals_history(
        self,
        access_token: str,
        account_id: str,
        from_timestamp_ms: int,
        to_timestamp_ms: int,
    ) -> list[dict]:
        """Get deal history for a time range."""
        if not self._connected:
            return []

        try:
            await _rate_limit()
            # In production, send ProtoOADealListReq
            # For now, return empty list
            return []
        except Exception as e:
            logger.error("Failed to get deals history: %s", e)
            return []

    async def health_check(self) -> tuple[bool, int]:
        """Ping cTrader API. Returns (connected, latency_ms)."""
        start = time.time()
        try:
            await _rate_limit()
            # In production, send a ping message
            latency = int((time.time() - start) * 1000)
            return True, latency
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return False, latency
