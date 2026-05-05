"""
CCXT Unified Connector
=======================
Normalizes Binance, Bybit, OKX, and other CEX venues into the
MASTER Trading typesystem.

Features:
- Automatic retry with exponential backoff
- Rate-limit compliance via CCXT's built-in throttle
- Normalized MarketData, Order, Position, ExecutionReport
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any

import ccxt.async_support as ccxt
from tenacity import retry, stop_after_attempt, wait_exponential

from skills.core.base import BaseConnector
from skills.core.types import ExecutionReport, MarketData, Order, OrderSide, Position


class CCXTConnector(BaseConnector):
    """Production-grade CEX connector using CCXT Pro."""

    name = "ccxt_unified_connector"
    description = "Unified CEX connectivity via CCXT async"
    version = "2.0.0"
    venue = "multi_cex"

    def __init__(
        self,
        exchange_id: str,
        api_key: str | None = None,
        api_secret: str | None = None,
        passphrase: str | None = None,
        sandbox: bool = True,
    ):
        self.exchange_id = exchange_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.sandbox = sandbox
        self._exchange: Any | None = None
        self._init_lock = asyncio.Lock()

    async def _client(self) -> Any:
        # Double-checked locking: avoid acquiring the lock once initialized,
        # but serialize concurrent first-time initializations so we never
        # construct two exchange clients (each loads markets, opens HTTP
        # sessions, and would race CCXT's internal rate-limit state).
        if self._exchange is not None:
            return self._exchange
        async with self._init_lock:
            if self._exchange is not None:
                return self._exchange
            cls = getattr(ccxt, self.exchange_id, None)
            if cls is None:
                raise ValueError(f"Exchange '{self.exchange_id}' not supported by CCXT")
            config: dict[str, Any] = {"enableRateLimit": True, "options": {}}
            if self.api_key:
                config["apiKey"] = self.api_key
            if self.api_secret:
                config["secret"] = self.api_secret
            if self.passphrase:
                config["password"] = self.passphrase
            if self.sandbox:
                config["sandbox"] = True
                config["options"]["defaultType"] = "swap"  # USDT-M perpetual default
            exchange = cls(config)
            await exchange.load_markets()
            self._exchange = exchange
            return self._exchange

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def fetch_ohlcv(
        self, symbol: str, timeframe: str = "1h", limit: int = 100
    ) -> list[MarketData]:
        ex = await self._client()
        raw = await ex.fetch_ohlcv(symbol, timeframe, limit=limit)
        return [
            MarketData(
                symbol=symbol,
                timestamp=ex.parse8601(ex.iso8601(candle[0])),
                open=Decimal(str(candle[1])),
                high=Decimal(str(candle[2])),
                low=Decimal(str(candle[3])),
                close=Decimal(str(candle[4])),
                volume=Decimal(str(candle[5])),
                quote_volume=Decimal(str(candle[6])) if len(candle) > 6 else Decimal("0"),
            )
            for candle in raw
        ]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def place_order(self, order: Order) -> ExecutionReport:
        ex = await self._client()
        side = order.side.value.lower()
        order_type = order.order_type.value.lower()
        amount = float(order.quantity)
        price = float(order.price) if order.price else None

        params: dict[str, Any] = {}
        if order.order_type.value in ("TWAP", "VWAP", "ICEBERG"):
            params["algoOrdType"] = order.order_type.value.lower()

        raw = await ex.create_order(order.symbol, order_type, side, amount, price, params)
        return self._normalize_execution(raw, order)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def cancel_order(self, order_id: str, symbol: str) -> ExecutionReport:
        ex = await self._client()
        await ex.cancel_order(order_id, symbol)
        return ExecutionReport(
            order=Order(
                symbol=symbol, side=OrderSide.SELL, order_type="MARKET", quantity=Decimal("0")
            ),
            status="CANCELLED",
        )

    async def fetch_position(self, symbol: str) -> Position | None:
        ex = await self._client()
        try:
            positions = await ex.fetch_positions([symbol])
            for p in positions:
                if p["symbol"] == symbol and float(p.get("contracts", 0)) != 0:
                    return Position(
                        symbol=symbol,
                        side="LONG" if p["side"] == "long" else "SHORT",
                        size=Decimal(str(p["contracts"])),
                        entry_price=Decimal(str(p["entryPrice"])),
                        unrealized_pnl=Decimal(str(p.get("unrealizedPnl", 0))),
                        leverage=Decimal(str(p.get("leverage", 1))),
                        liquidation_price=(
                            Decimal(str(p.get("liquidationPrice", 0)))
                            if p.get("liquidationPrice")
                            else None
                        ),
                    )
        except Exception:
            pass
        return None

    def _normalize_execution(self, raw: dict, order: Order) -> ExecutionReport:
        status_map = {
            "open": "OPEN",
            "closed": "FILLED",
            "canceled": "CANCELLED",
            "cancelled": "CANCELLED",
            "rejected": "REJECTED",
            "expired": "EXPIRED",
        }
        return ExecutionReport(
            order=order,
            status=status_map.get(raw.get("status", "").lower(), "PENDING"),
            total_filled=Decimal(str(raw.get("filled", 0))),
            remaining=Decimal(str(raw.get("remaining", 0))),
            avg_fill_price=Decimal(str(raw.get("average", 0))) if raw.get("average") else None,
        )

    async def run(self, context: dict[str, Any]) -> Any:
        """Agent dispatch entrypoint."""
        action = context.get("action")
        if action == "ohlcv":
            return await self.fetch_ohlcv(
                context["symbol"],
                context.get("timeframe", "1h"),
                context.get("limit", 100),
            )
        elif action == "place_order":
            from skills.core.types import Order

            return await self.place_order(Order(**context["order"]))
        elif action == "cancel_order":
            return await self.cancel_order(context["order_id"], context["symbol"])
        elif action == "position":
            return await self.fetch_position(context["symbol"])
        else:
            raise ValueError(f"Unknown action: {action}")

    async def close(self) -> None:
        if self._exchange:
            await self._exchange.close()
            self._exchange = None
