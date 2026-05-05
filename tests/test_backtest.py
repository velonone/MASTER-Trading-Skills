"""
Unit tests for backtest engine — Vectorized Strategy Validation.
"""

import numpy as np
import pandas as pd
import pytest

from backtest import BacktestEngine, VolatilitySlippage
from skills.core.types import Signal, SignalAction


class MockStrategy:
    """Simple momentum strategy for testing."""

    def generate_signals(self, bar: dict) -> list:
        # Buy if close > open, sell if close < open
        if bar["close"] > bar["open"]:
            return [
                Signal(
                    action=SignalAction.BUY,
                    confidence=0.8,
                    strength=0.5,
                    symbol="BTC/USDT",
                    source="mock",
                )
            ]
        elif bar["close"] < bar["open"]:
            return [
                Signal(
                    action=SignalAction.SELL,
                    confidence=0.8,
                    strength=0.5,
                    symbol="BTC/USDT",
                    source="mock",
                )
            ]
        return []


@pytest.fixture
def sample_data():
    np.random.seed(42)
    n = 100
    dates = pd.date_range("2024-01-01", periods=n, freq="h")
    trend = np.cumsum(np.random.randn(n) * 10)
    opens = 50000 + trend
    closes = opens + np.random.randn(n) * 50
    highs = np.maximum(opens, closes) + np.abs(np.random.randn(n)) * 30
    lows = np.minimum(opens, closes) - np.abs(np.random.randn(n)) * 30
    volumes = np.abs(np.random.randn(n)) * 100 + 50
    return pd.DataFrame(
        {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        },
        index=dates,
    )


def test_backtest_runs(sample_data):
    engine = BacktestEngine(
        data=sample_data,
        strategy=MockStrategy(),
        initial_capital=100_000,
    )
    result = engine.run()
    assert result.trades > 0
    assert len(result.equity_curve) == len(sample_data)


def test_backtest_equity_monotonic_with_simple_strategy():
    # Rising market: always buy
    df = pd.DataFrame(
        {
            "open": [100, 101, 102, 103, 104],
            "high": [101, 102, 103, 104, 105],
            "low": [99, 100, 101, 102, 103],
            "close": [101, 102, 103, 104, 105],
            "volume": [100, 100, 100, 100, 100],
        }
    )

    class AlwaysBuy:
        def generate_signals(self, bar):
            return [
                Signal(
                    action=SignalAction.BUY,
                    confidence=1.0,
                    strength=1.0,
                    symbol="TEST",
                    source="test",
                )
            ]

    engine = BacktestEngine(data=df, strategy=AlwaysBuy(), initial_capital=10000)
    result = engine.run()
    assert result.total_return > 0
    assert result.equity_curve.iloc[-1] > result.equity_curve.iloc[0]


def test_backtest_metrics_computed(sample_data):
    engine = BacktestEngine(data=sample_data, strategy=MockStrategy(), initial_capital=100_000)
    result = engine.run()
    assert isinstance(result.sharpe_ratio, float)
    assert isinstance(result.max_drawdown, float)
    assert result.max_drawdown <= 0.0


def test_volatility_slippage():
    model = VolatilitySlippage(base_bps=2.0, volatility_factor=5.0)
    bar = {"close": 50000, "high": 50100, "low": 49900, "volume": 1000, "atr_14": 200}
    slip = model.apply(order_qty=10, bar=bar, side="buy")
    assert slip >= 2.0


def test_broker_limit_order_fill():
    from backtest.broker import BrokerSimulator

    broker = BrokerSimulator()
    bar = {"open": 100, "high": 105, "low": 95, "close": 102, "volume": 1000}
    fill = broker.simulate_limit_order(qty=1.0, limit_price=96, bar=bar, side="buy")
    assert fill is not None
    assert fill.price <= 96


def test_broker_limit_order_no_fill():
    from backtest.broker import BrokerSimulator

    broker = BrokerSimulator()
    bar = {"open": 100, "high": 105, "low": 99, "close": 102, "volume": 1000}
    fill = broker.simulate_limit_order(qty=1.0, limit_price=95, bar=bar, side="buy")
    assert fill is None


def test_broker_limit_order_open_already_crossed():
    """Buy limit above open — fills at open (no lookahead needed)."""
    from backtest.broker import BrokerSimulator

    broker = BrokerSimulator()
    bar = {"open": 94, "high": 105, "low": 90, "close": 102, "volume": 1000}
    fill = broker.simulate_limit_order(qty=1.0, limit_price=95, bar=bar, side="buy")
    assert fill is not None
    assert fill.price == 94  # filled at open, not better than limit


def test_broker_limit_order_range_crossed_later():
    """Open above limit, but low touches limit — fills at limit price."""
    from backtest.broker import BrokerSimulator

    broker = BrokerSimulator()
    bar = {"open": 100, "high": 105, "low": 95, "close": 102, "volume": 1000}
    fill = broker.simulate_limit_order(qty=1.0, limit_price=95, bar=bar, side="buy")
    assert fill is not None
    assert fill.price == 95  # conservative fill at limit, not at low


def test_broker_limit_order_sell_open_crossed():
    """Sell limit below open — fills at open."""
    from backtest.broker import BrokerSimulator

    broker = BrokerSimulator()
    bar = {"open": 106, "high": 110, "low": 100, "close": 102, "volume": 1000}
    fill = broker.simulate_limit_order(qty=1.0, limit_price=105, bar=bar, side="sell")
    assert fill is not None
    assert fill.price == 106


def test_broker_limit_order_sell_range_crossed():
    """Open below limit, but high touches limit — fills at limit price."""
    from backtest.broker import BrokerSimulator

    broker = BrokerSimulator()
    bar = {"open": 100, "high": 110, "low": 95, "close": 102, "volume": 1000}
    fill = broker.simulate_limit_order(qty=1.0, limit_price=105, bar=bar, side="sell")
    assert fill is not None
    assert fill.price == 105


def test_backtest_no_lookahead_oracle_strategy():
    """
    Regression: a perfect-foresight strategy that buys whenever close>open
    must NOT achieve riskless profit, because fills happen on the *next*
    bar's open. If it does, lookahead has crept back in.
    """
    # Construct: every other bar has close>open; the bar AFTER opens
    # below the previous close, so a perfect-foresight strategy that
    # exploits same-bar fills would show >0 return; next-bar fills must
    # produce roughly zero or negative return (no oracle profit).
    df = pd.DataFrame(
        {
            "open": [100, 110, 100, 110, 100, 110, 100, 110, 100, 110],
            "high": [120, 110, 120, 110, 120, 110, 120, 110, 120, 110],
            "low": [100, 100, 100, 100, 100, 100, 100, 100, 100, 100],
            "close": [115, 100, 115, 100, 115, 100, 115, 100, 115, 100],
            "volume": [100] * 10,
        }
    )

    class OracleSameBar:
        """Buys whenever the bar's close exceeds open — pure lookahead."""

        def generate_signals(self, bar):
            if bar["close"] > bar["open"]:
                return [
                    Signal(
                        action=SignalAction.BUY,
                        confidence=1.0,
                        strength=1.0,
                        symbol="X",
                        source="oracle",
                    )
                ]
            return [
                Signal(
                    action=SignalAction.CLOSE,
                    confidence=1.0,
                    strength=1.0,
                    symbol="X",
                    source="oracle",
                )
            ]

    engine = BacktestEngine(
        data=df,
        strategy=OracleSameBar(),
        initial_capital=10_000,
        commission=0.0,
        slippage_model=_ZeroSlippage(),
    )
    result = engine.run()
    # If lookahead exists, the oracle would print money. With next-bar
    # fills the buy executes at the next bar's open=110 and the close
    # mark is 100 — the strategy must lose, not win.
    assert result.total_return <= 0, (
        f"Oracle strategy still profits ({result.total_return:.4f}); "
        "lookahead bias has not been fully eliminated."
    )


class _ZeroSlippage:
    def apply(self, order_qty, bar, side):
        return 0.0
