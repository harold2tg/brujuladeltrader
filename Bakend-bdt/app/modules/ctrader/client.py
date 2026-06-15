"""cTrader Open API client — real TCP/Protobuf implementation.

Uses the official ctrader-open-api protobuf messages and the correct wire format:
- 4-byte big-endian length prefix (Int32StringReceiver format)
- Serialized ProtoMessage containing payloadType + payload
"""

import asyncio
import logging
import ssl
import struct
import time

from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import ProtoMessage
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq,
    ProtoOAAccountAuthReq,
    ProtoOAGetAccountListByAccessTokenReq,
    ProtoOAGetAccountListByAccessTokenRes,
    ProtoOADealListReq,
    ProtoOADealListRes,
    ProtoOASymbolsListReq,
    ProtoOASymbolsListRes,
)

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


def _build_wrapped_message(inner_message) -> bytes:
    """Wrap an inner protobuf message in ProtoMessage and serialize.
    
    The cTrader wire format uses Twisted's Int32StringReceiver:
    - 4 bytes: length of serialized ProtoMessage (big-endian)
    - ProtoMessage bytes: { payloadType: inner.payloadType, payload: inner.SerializeToString() }
    """
    msg = ProtoMessage(
        payload=inner_message.SerializeToString(),
        payloadType=inner_message.payloadType,
    )
    return msg.SerializeToString()


class CtraderClient:
    """Real cTrader Open API client via TCP/Protobuf."""

    def __init__(self, host: str, port: int, is_demo: bool = False):
        self.host = host
        self.port = port
        self.is_demo = is_demo
        self._reader = None
        self._writer = None
        self._connected = False
        self._authenticated = False

    async def connect(self) -> bool:
        """Connect to cTrader TCP endpoint with SSL/TLS."""
        try:
            ssl_context = ssl.create_default_context()

            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(
                    self.host,
                    self.port,
                    ssl=ssl_context,
                    server_hostname=self.host,
                ),
                timeout=10,
            )
            self._connected = True
            logger.info("Connected to cTrader (SSL) at %s:%d", self.host, self.port)
            return True
        except Exception as e:
            logger.error("Failed to connect to cTrader: %s", e)
            self._connected = False
            return False

    async def disconnect(self):
        """Disconnect from cTrader."""
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
        self._connected = False
        self._authenticated = False

    async def _send_and_receive(self, inner_message) -> tuple[int, bytes]:
        """Send a protobuf message and receive response.
        
        Wire format (Twisted Int32StringReceiver):
        - Send: [4-byte length][serialized ProtoMessage]
        - Recv: [4-byte length][serialized ProtoMessage]
        """
        if not self._connected or not self._writer:
            raise ConnectionError("Not connected to cTrader")

        await _rate_limit()

        # Build the wire message: 4-byte length prefix + ProtoMessage
        payload = _build_wrapped_message(inner_message)
        wire_msg = struct.pack(">I", len(payload)) + payload

        self._writer.write(wire_msg)
        await self._writer.drain()

        # Read response: 4-byte length prefix
        len_bytes = await asyncio.wait_for(self._reader.readexactly(4), timeout=30)
        resp_len = struct.unpack(">I", len_bytes)[0]

        if resp_len > 15_000_000:
            raise ValueError(f"Response too large: {resp_len} bytes")

        # Read the ProtoMessage bytes
        resp_data = await asyncio.wait_for(self._reader.readexactly(resp_len), timeout=30)

        # Parse ProtoMessage
        proto_msg = ProtoMessage()
        proto_msg.ParseFromString(resp_data)

        return proto_msg.payloadType, proto_msg.payload

    async def authenticate_app(self, client_id: str, client_secret: str) -> bool:
        """Authenticate the application."""
        req = ProtoOAApplicationAuthReq(
            clientId=client_id,
            clientSecret=client_secret,
        )

        try:
            resp_type, resp_body = await self._send_and_receive(req)
            if resp_type == 2101:  # ProtoOAApplicationAuthRes
                logger.info("Application authenticated successfully")
                return True
            else:
                logger.error("Application auth failed, response type: %d", resp_type)
                return False
        except Exception as e:
            logger.error("Application auth error: %s", e)
            return False

    async def authenticate_account(self, access_token: str, account_id: str) -> bool:
        """Authenticate the trading account."""
        req = ProtoOAAccountAuthReq(
            ctidTraderAccountId=int(account_id),
            accessToken=access_token,
        )

        try:
            resp_type, resp_body = await self._send_and_receive(req)
            if resp_type == 2103:  # ProtoOAAccountAuthRes
                logger.info("Account authenticated successfully")
                self._authenticated = True
                return True
            else:
                logger.error("Account auth failed, response type: %d", resp_type)
                return False
        except Exception as e:
            logger.error("Account auth error: %s", e)
            return False

    async def get_accounts(self, access_token: str) -> list[dict]:
        """Get accounts by access token.
        
        Returns list of dicts with keys: account_id (str), is_live (bool), trader_login (int).
        """
        req = ProtoOAGetAccountListByAccessTokenReq(
            accessToken=access_token,
        )

        try:
            resp_type, resp_body = await self._send_and_receive(req)
            if resp_type == 2150:  # ProtoOAGetAccountListByAccessTokenRes
                res = ProtoOAGetAccountListByAccessTokenRes()
                res.ParseFromString(resp_body)

                accounts = []
                for acct in res.ctidTraderAccount:
                    accounts.append({
                        "account_id": str(acct.ctidTraderAccountId),
                        "is_live": acct.isLive,
                        "trader_login": acct.traderLogin,
                    })
                return accounts
            else:
                logger.warning("Unexpected accounts response type: %d", resp_type)
                return []
        except Exception as e:
            logger.error("Get accounts error: %s", e)
            return []

    async def get_symbols(self, account_id: str) -> dict[int, str]:
        """Get symbol list and return mapping {symbolId: symbolName}.
        
        Requires account to be authenticated first.
        """
        req = ProtoOASymbolsListReq(
            ctidTraderAccountId=int(account_id),
        )

        try:
            resp_type, resp_body = await self._send_and_receive(req)
            if resp_type == 2115:  # ProtoOASymbolsListRes
                res = ProtoOASymbolsListRes()
                res.ParseFromString(resp_body)

                symbols = {}
                for sym in res.symbol:
                    symbols[sym.symbolId] = sym.symbolName
                return symbols
            else:
                logger.warning("Unexpected symbols response type: %d", resp_type)
                return {}
        except Exception as e:
            logger.error("Get symbols error: %s", e)
            return {}

    async def get_deals_history(
        self,
        access_token: str,
        account_id: str,
        from_timestamp_ms: int,
        to_timestamp_ms: int,
    ) -> list[dict]:
        """Get deal history from cTrader.
        
        Returns list of deal dicts with all fields from ProtoOADeal + closePositionDetail.
        """
        req = ProtoOADealListReq(
            ctidTraderAccountId=int(account_id),
            fromTimestamp=from_timestamp_ms,
            toTimestamp=to_timestamp_ms,
        )

        try:
            resp_type, resp_body = await self._send_and_receive(req)
            if resp_type == 2134:  # ProtoOADealListRes
                res = ProtoOADealListRes()
                res.ParseFromString(resp_body)

                deals = []
                for deal in res.deal:
                    deal_dict = {
                        "dealId": deal.dealId,
                        "orderId": deal.orderId,
                        "positionId": deal.positionId,
                        "volume": deal.volume,
                        "filledVolume": deal.filledVolume,
                        "symbolId": deal.symbolId,
                        "createTimestamp": deal.createTimestamp,
                        "executionTimestamp": deal.executionTimestamp,
                        "executionPrice": deal.executionPrice,
                        "tradeSide": deal.tradeSide,  # 1=BUY, 2=SELL
                        "dealStatus": deal.dealStatus,
                        "commission": deal.commission,
                        "moneyDigits": deal.moneyDigits,
                    }

                    # Add close position detail if present
                    if deal.HasField("closePositionDetail"):
                        detail = deal.closePositionDetail
                        deal_dict["isClose"] = True
                        deal_dict["entryPrice"] = detail.entryPrice
                        deal_dict["grossProfit"] = detail.grossProfit
                        deal_dict["swap"] = detail.swap
                        deal_dict["commissionDetail"] = detail.commission
                        deal_dict["balance"] = detail.balance
                        deal_dict["closedVolume"] = detail.closedVolume
                    else:
                        deal_dict["isClose"] = False

                    deals.append(deal_dict)

                logger.info("Retrieved %d deals", len(deals))
                return deals
            else:
                logger.warning("Unexpected deals response type: %d", resp_type)
                return []
        except Exception as e:
            logger.error("Get deals history error: %s", e)
            return []


async def health_check(host: str, port: int) -> tuple[bool, int]:
    """Check if cTrader API is reachable."""
    start = time.time()
    try:
        ssl_context = ssl.create_default_context()
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(
                host, port,
                ssl=ssl_context,
                server_hostname=host,
            ),
            timeout=5,
        )
        writer.close()
        await writer.wait_closed()
        latency = int((time.time() - start) * 1000)
        return True, latency
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        logger.error("Health check failed: %s", e)
        return False, latency
