"""
Unit tests for skills.core.types and skills.core.base — the universal type system and base classes.
"""

import pytest
from decimal import Decimal
from skills.core.types import Signal, SignalAction, MarketData, Order, OrderSide, OrderType, Position
from skills.core.base import BaseSkill
from skills.signals.technical.kelly import KellyPositionSizer


class MinimalSkill(BaseSkill):
    """Concrete skill for testing BaseSkill lifecycle defaults."""
    name = "minimal"
    description = "Test skill"
    version = "0.0.1"

    async def run(self, context):
        return "ok"


@pytest.mark.asyncio
async def test_base_skill_lifecycle_defaults():
    """BaseSkill subclasses should work without overriding start/stop/health."""
    skill = MinimalSkill()
    await skill.start()
    await skill.stop()
    health = skill.health()
    assert health["status"] == "ok"
    assert health["skill"] == "minimal"
    assert health["version"] == "0.0.1"


def test_signal_validation():
    s = Signal(
        action=SignalAction.BUY,
        confidence=0.85,
        strength=0.7,
        symbol="BTC/USDT",
        source="test",
        evidence=["OBI bullish"],
    )
    assert s.action == SignalAction.BUY
    assert s.confidence == 0.85
    assert s.symbol == "BTC/USDT"


def test_signal_clamping():
    s = Signal(action=SignalAction.SELL, confidence=1.5, strength=-0.2, symbol="ETH/USDT", source="test")
    assert s.confidence == 1.0
    assert s.strength == 0.0


def test_market_data_decimal():
    md = MarketData(
        symbol="BTC/USDT",
        timestamp="2024-01-01T00:00:00",
        open=Decimal("50000"),
        high=Decimal("51000"),
        low=Decimal("49500"),
        close=Decimal("50500"),
        volume=Decimal("100"),
        quote_volume=Decimal("5000000"),
    )
    assert md.close == Decimal("50500")


def test_order_creation():
    o = Order(symbol="BTC/USDT", side=OrderSide.BUY, order_type=OrderType.LIMIT, quantity=Decimal("0.5"), price=Decimal("50000"))
    assert o.side == OrderSide.BUY
    assert o.order_type == OrderType.LIMIT


def test_position_pnl():
    p = Position(symbol="BTC/USDT", side="LONG", size=Decimal("1.0"), entry_price=Decimal("50000"), unrealized_pnl=Decimal("500"))
    assert p.side == "LONG"


def test_kelly_sizing():
    k = KellyPositionSizer(fraction=0.25, max_position_pct=0.20)
    size = k.compute(win_rate=0.55, win_loss_ratio=2.0)
    assert size is not None
    assert size > Decimal("0")
    assert size <= Decimal("0.20")
