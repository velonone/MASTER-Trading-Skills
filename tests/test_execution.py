"""
Unit tests for skills.execution — OMS & Risk Management.
"""

from decimal import Decimal

import pytest

from skills.core.types import Order, OrderSide, OrderType, RiskLimit, Signal, SignalAction
from skills.execution.oms import OrderManagementSystem
from skills.execution.risk import DynamicRiskManager


@pytest.mark.asyncio
async def test_oms_order_submission():
    oms = OrderManagementSystem()
    order = Order(
        symbol="BTC/USDT", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=Decimal("0.1")
    )
    oid = await oms.submit(order)
    assert oid.startswith("mt-")
    assert oms.orders[oid].symbol == "BTC/USDT"


@pytest.mark.asyncio
async def test_oms_position_reconciliation():
    oms = OrderManagementSystem()
    from skills.core.types import ExecutionReport

    order = Order(
        id="test-1",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("1.0"),
    )
    report = ExecutionReport(
        order=order,
        status="FILLED",
        total_filled=Decimal("1.0"),
        avg_fill_price=Decimal("50000"),
    )
    await oms.on_report(report)
    pos = oms.position("BTC/USDT")
    assert pos is not None
    assert pos.size == Decimal("1.0")


@pytest.mark.asyncio
async def test_risk_manager_blocks_low_confidence():
    risk = DynamicRiskManager()
    signal = Signal(action=SignalAction.BUY, confidence=0.30, symbol="BTC/USDT", source="test")
    result = await risk.evaluate_signal(signal, position=None)
    assert result.action == SignalAction.HOLD


@pytest.mark.asyncio
async def test_risk_manager_allows_high_confidence():
    risk = DynamicRiskManager()
    signal = Signal(action=SignalAction.BUY, confidence=0.90, symbol="BTC/USDT", source="test")
    result = await risk.evaluate_signal(signal, position=None)
    assert result.action == SignalAction.BUY


@pytest.mark.asyncio
async def test_risk_velocity_limit():
    risk = DynamicRiskManager(
        limits=RiskLimit(max_position_size=Decimal("10"), max_orders_per_minute=2)
    )
    order = Order(
        symbol="BTC/USDT", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=Decimal("1.0")
    )
    o1 = await risk.evaluate_order(order)
    o2 = await risk.evaluate_order(order)
    o3 = await risk.evaluate_order(order)
    assert o1 is not None
    assert o2 is not None
    assert o3 is None  # velocity cap


def test_signal_to_order_conversion():
    oms = OrderManagementSystem()
    signal = Signal(action=SignalAction.SELL, confidence=0.85, symbol="ETH/USDT", source="test")
    order = oms.signal_to_order(signal, qty=Decimal("0.5"), order_type="LIMIT")
    assert order.side == OrderSide.SELL
    assert order.symbol == "ETH/USDT"
    assert order.quantity == Decimal("0.5")


# ---------------------------------------------------------------------------
# OMS realized-PnL: long/short/flip branches must be correct
# ---------------------------------------------------------------------------


def _fill(oid: str, symbol: str, side: OrderSide, qty: str, price: str):
    from skills.core.types import ExecutionReport

    order = Order(
        id=oid, symbol=symbol, side=side, order_type=OrderType.MARKET, quantity=Decimal(qty)
    )
    return ExecutionReport(
        order=order,
        status="FILLED",
        total_filled=Decimal(qty),
        avg_fill_price=Decimal(price),
    )


@pytest.mark.asyncio
async def test_oms_realized_pnl_long_close_profit():
    """Long entry at 100, close at 120 → realized PnL = +20 per unit."""
    oms = OrderManagementSystem()
    await oms.on_report(_fill("o1", "X", OrderSide.BUY, "1", "100"))
    await oms.on_report(_fill("o2", "X", OrderSide.SELL, "1", "120"))
    pos = oms.position("X")
    assert pos.size == Decimal("0")
    assert pos.side == "FLAT"
    assert pos.realized_pnl == Decimal("20")


@pytest.mark.asyncio
async def test_oms_realized_pnl_short_close_profit():
    """Short entry at 100, cover at 80 → realized PnL = +20 per unit."""
    oms = OrderManagementSystem()
    await oms.on_report(_fill("o1", "X", OrderSide.SELL, "1", "100"))
    await oms.on_report(_fill("o2", "X", OrderSide.BUY, "1", "80"))
    pos = oms.position("X")
    assert pos.size == Decimal("0")
    assert pos.side == "FLAT"
    assert pos.realized_pnl == Decimal("20")


@pytest.mark.asyncio
async def test_oms_realized_pnl_long_partial_close():
    """Long 2 @ 100, sell 1 @ 110 → realized +10, position 1 long @ 100."""
    oms = OrderManagementSystem()
    await oms.on_report(_fill("o1", "X", OrderSide.BUY, "2", "100"))
    await oms.on_report(_fill("o2", "X", OrderSide.SELL, "1", "110"))
    pos = oms.position("X")
    assert pos.size == Decimal("1")
    assert pos.side == "LONG"
    assert pos.entry_price == Decimal("100")
    assert pos.realized_pnl == Decimal("10")


@pytest.mark.asyncio
async def test_oms_realized_pnl_long_to_short_flip():
    """
    Long 1 @ 100, sell 3 @ 120 →
      - Closing portion (1 unit): realized +20
      - Flip portion (2 units): new short entry @ 120
    """
    oms = OrderManagementSystem()
    await oms.on_report(_fill("o1", "X", OrderSide.BUY, "1", "100"))
    await oms.on_report(_fill("o2", "X", OrderSide.SELL, "3", "120"))
    pos = oms.position("X")
    assert pos.size == Decimal("-2")
    assert pos.side == "SHORT"
    assert pos.entry_price == Decimal("120")
    assert pos.realized_pnl == Decimal("20")


@pytest.mark.asyncio
async def test_oms_weighted_entry_price_on_add():
    """Long 1 @ 100, then long 1 @ 200 → entry = 150 (weighted avg)."""
    oms = OrderManagementSystem()
    await oms.on_report(_fill("o1", "X", OrderSide.BUY, "1", "100"))
    await oms.on_report(_fill("o2", "X", OrderSide.BUY, "1", "200"))
    pos = oms.position("X")
    assert pos.size == Decimal("2")
    assert pos.entry_price == Decimal("150")
    assert pos.realized_pnl == Decimal("0")
