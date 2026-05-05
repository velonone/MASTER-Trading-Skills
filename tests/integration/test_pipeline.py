"""
Integration tests for skills.execution.pipeline.TradingPipeline.

These exercise the canonical Signal -> Risk -> OMS -> Connector seam end
to end. We use stub strategies and an in-memory connector to avoid network
or RPC dependencies.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

import pytest

from skills.core.base import BaseConnector, BaseStrategy
from skills.core.types import (
    ExecutionReport,
    MarketData,
    Order,
    OrderSide,
    Position,
    Signal,
    SignalAction,
)
from skills.execution import (
    DynamicRiskManager,
    OrderManagementSystem,
    TradingPipeline,
    fixed_qty_sizer,
)


class _AlwaysBuy(BaseStrategy):
    name = "always_buy"

    def generate_signals(self, context: Dict[str, Any]) -> List[Signal]:
        return [Signal(
            action=SignalAction.BUY, confidence=0.9, strength=1.0,
            symbol=context.get("symbol", "BTC/USDT"), source=self.name,
        )]


class _AlwaysHold(BaseStrategy):
    name = "always_hold"

    def generate_signals(self, context: Dict[str, Any]) -> List[Signal]:
        return [Signal(
            action=SignalAction.HOLD, confidence=0.0,
            symbol=context.get("symbol", "BTC/USDT"), source=self.name,
        )]


class _MemoryConnector(BaseConnector):
    """Trivial in-memory connector that always reports a complete fill."""
    name = "memory_connector"
    venue = "test"

    def __init__(self, fill_price: Decimal = Decimal("100")):
        self.fill_price = fill_price
        self.orders_received: List[Order] = []

    async def fetch_ohlcv(self, symbol, timeframe="1h", limit=100):
        return []

    async def place_order(self, order: Order) -> ExecutionReport:
        self.orders_received.append(order)
        return ExecutionReport(
            order=order,
            status="FILLED",
            total_filled=order.quantity,
            avg_fill_price=self.fill_price,
        )

    async def cancel_order(self, order_id, symbol):
        return ExecutionReport(
            order=Order(symbol=symbol, side=OrderSide.SELL,
                        order_type="MARKET", quantity=Decimal("0")),
            status="CANCELLED",
        )

    async def fetch_position(self, symbol):
        return None

    async def run(self, context):
        return {"ok": True}


@pytest.mark.asyncio
async def test_pipeline_signal_to_fill_end_to_end():
    """A buy signal must traverse risk + OMS + connector and update position."""
    oms = OrderManagementSystem()
    connector = _MemoryConnector(fill_price=Decimal("100"))
    pipeline = TradingPipeline(
        strategy=_AlwaysBuy(),
        risk=DynamicRiskManager(),
        oms=oms,
        connector=connector,
        sizer=fixed_qty_sizer(Decimal("0.5")),
    )

    result = await pipeline.process({"symbol": "BTC/USDT"})

    assert len(result.steps) == 1
    step = result.steps[0]
    assert step.report is not None
    assert step.report.status == "FILLED"
    assert step.rejected_reason is None
    assert connector.orders_received[0].quantity == Decimal("0.5")

    pos = oms.position("BTC/USDT")
    assert pos is not None
    assert pos.size == Decimal("0.5")
    assert pos.side == "LONG"
    assert pos.entry_price == Decimal("100")


@pytest.mark.asyncio
async def test_pipeline_hold_short_circuits_before_connector():
    """A HOLD signal must not place an order on the connector."""
    connector = _MemoryConnector()
    pipeline = TradingPipeline(
        strategy=_AlwaysHold(),
        risk=DynamicRiskManager(),
        oms=OrderManagementSystem(),
        connector=connector,
        sizer=fixed_qty_sizer(Decimal("1")),
    )
    result = await pipeline.process({"symbol": "BTC/USDT"})
    assert result.steps[0].rejected_reason == "HOLD"
    assert connector.orders_received == []


@pytest.mark.asyncio
async def test_pipeline_risk_blocks_low_confidence_signal():
    """Risk manager downgrades the signal to HOLD; connector must not see it."""

    class _LowConfBuy(BaseStrategy):
        name = "low_conf_buy"

        def generate_signals(self, ctx):
            return [Signal(action=SignalAction.BUY, confidence=0.30,
                           symbol="BTC/USDT", source=self.name)]

    connector = _MemoryConnector()
    pipeline = TradingPipeline(
        strategy=_LowConfBuy(),
        risk=DynamicRiskManager(),
        oms=OrderManagementSystem(),
        connector=connector,
        sizer=fixed_qty_sizer(Decimal("1")),
    )
    result = await pipeline.process({"symbol": "BTC/USDT"})
    assert result.steps[0].rejected_reason == "RISK_BLOCKED_SIGNAL"
    assert connector.orders_received == []


@pytest.mark.asyncio
async def test_oms_persistence_round_trip(tmp_path):
    """
    Snapshot → save → load through a fresh OMS produces identical state.
    Prevents the 'process restart erases everything' regression.
    """
    oms = OrderManagementSystem()
    pipeline = TradingPipeline(
        strategy=_AlwaysBuy(),
        risk=DynamicRiskManager(),
        oms=oms,
        connector=_MemoryConnector(fill_price=Decimal("123.45")),
        sizer=fixed_qty_sizer(Decimal("0.5")),
    )
    await pipeline.process({"symbol": "ETH/USDT"})

    path = tmp_path / "oms_state.json"
    oms.save(path)
    assert path.exists()

    restored = OrderManagementSystem.from_file(path)
    pos = restored.position("ETH/USDT")
    assert pos is not None
    assert pos.size == Decimal("0.5")
    assert pos.entry_price == Decimal("123.45")
    assert len(restored.orders) == len(oms.orders)
    assert len(restored.reports) == len(oms.reports)


@pytest.mark.asyncio
async def test_oms_from_file_missing_path_returns_empty(tmp_path):
    """Crash-recovery: a missing snapshot path yields an empty OMS, not an error."""
    oms = OrderManagementSystem.from_file(tmp_path / "does_not_exist.json")
    assert oms.all_positions() == []
