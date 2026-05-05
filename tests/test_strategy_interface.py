"""
Tests for unified BaseStrategy signal seam (P1).
"""

import pandas as pd
import pytest

from backtest.engine import BacktestEngine
from skills.core.base import BaseSkill, BaseStrategy
from skills.core.types import Signal, SignalAction
from skills.signals.technical.funding_arb import FundingArbitrageSignal
from skills.signals.technical.obi import OrderBookImbalance


class DummyStrategy(BaseStrategy):
    """Minimal strategy for testing the BaseStrategy interface."""

    name = "dummy"

    def generate_signals(self, context: dict) -> list:
        return [
            Signal(
                action=SignalAction.BUY,
                confidence=0.8,
                strength=0.5,
                symbol="BTC/USDT",
                source=self.name,
                evidence=["dummy"],
            )
        ]


def test_base_strategy_is_abstract():
    """BaseStrategy cannot be instantiated without generate_signals."""
    with pytest.raises(TypeError):
        BaseStrategy()


@pytest.mark.asyncio
async def test_base_strategy_run_delegates_to_generate_signals():
    """run() should delegate to generate_signals()."""
    s = DummyStrategy()
    result = await s.run({})
    assert isinstance(result, list)
    assert result[0].action == SignalAction.BUY


def test_obi_inherits_base_strategy():
    """OrderBookImbalance should be a BaseStrategy."""
    obi = OrderBookImbalance()
    assert isinstance(obi, BaseStrategy)
    assert isinstance(obi, BaseSkill)


def test_obi_generate_signals_from_context():
    """OBI should generate signals via the unified generate_signals interface."""
    obi = OrderBookImbalance()
    signals = obi.generate_signals(
        {
            "symbol": "BTC/USDT",
            "bids": [[65000, 5.0], [64990, 3.2]],
            "asks": [[65010, 1.5], [65020, 4.0]],
        }
    )
    assert isinstance(signals, list)
    assert signals[0].symbol == "BTC/USDT"


def test_funding_arb_inherits_base_strategy():
    """FundingArbitrageSignal should be a BaseStrategy."""
    fa = FundingArbitrageSignal()
    assert isinstance(fa, BaseStrategy)
    assert isinstance(fa, BaseSkill)


def test_funding_arb_generate_signals_from_context():
    """FundingArb should generate signals via the unified interface."""
    fa = FundingArbitrageSignal()
    signals = fa.generate_signals(
        {
            "symbol": "BTC/USDT",
            "funding_rate": -0.0005,
        }
    )
    assert isinstance(signals, list)
    assert signals[0].action == SignalAction.BUY


def test_backtest_accepts_base_strategy():
    """BacktestEngine should accept BaseStrategy instances."""
    df = pd.DataFrame(
        {
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "volume": [1000.0, 2000.0],
        }
    )
    strategy = DummyStrategy()
    engine = BacktestEngine(data=df, strategy=strategy, initial_capital=100_000)
    result = engine.run()
    assert result.trades > 0
