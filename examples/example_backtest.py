#!/usr/bin/env python3
"""
Example: Vectorized Backtest with Simple Momentum Strategy
===========================================================
Run with: python examples/example_backtest.py
"""

import numpy as np
import pandas as pd

from backtest import BacktestEngine, VolatilitySlippage
from skills.core.types import Signal, SignalAction


class MeanReversionStrategy:
    """Simple mean reversion: buy after down move, sell after up move."""

    name = "mean_reversion_example"

    def generate(self, bar: dict) -> list:
        if bar["close"] < bar["open"] * 0.998:  # down move > 0.2%
            return [
                Signal(
                    action=SignalAction.BUY,
                    confidence=0.6,
                    strength=0.3,
                    symbol="BTC/USDT",
                    source=self.name,
                    evidence=[f"Down candle: {bar['close']:.0f} < {bar['open']:.0f}"],
                )
            ]
        elif bar["close"] > bar["open"] * 1.002:  # up move > 0.2%
            return [
                Signal(
                    action=SignalAction.SELL,
                    confidence=0.6,
                    strength=0.3,
                    symbol="BTC/USDT",
                    source=self.name,
                    evidence=[f"Up candle: {bar['close']:.0f} > {bar['open']:.0f}"],
                )
            ]
        return []


def generate_sample_data(n: int = 500) -> pd.DataFrame:
    """Generate synthetic OHLCV data for demonstration."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="h")
    opens = 50000 + np.cumsum(np.random.randn(n) * 10)
    closes = opens + np.random.randn(n) * 50
    highs = np.maximum(opens, closes) + np.abs(np.random.randn(n)) * 30
    lows = np.minimum(opens, closes) - np.abs(np.random.randn(n)) * 30
    volumes = np.abs(np.random.randn(n)) * 100 + 50
    return pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes},
        index=dates,
    )


def main():
    print("=" * 60)
    print("MASTER Trading — Backtest Example")
    print("=" * 60)

    df = generate_sample_data(500)
    print(f"\nData: {len(df)} bars from {df.index[0]} to {df.index[-1]}")

    engine = BacktestEngine(
        data=df,
        strategy=MeanReversionStrategy(),
        initial_capital=100_000,
        commission=0.0004,
        slippage_model=VolatilitySlippage(base_bps=2.0),
    )

    result = engine.run()

    print(f"\nResults:")
    print(f"  Total Return:     {result.total_return:+.2%}")
    print(f"  Sharpe Ratio:     {result.sharpe_ratio:.3f}")
    print(f"  Sortino Ratio:    {result.sortino_ratio:.3f}")
    print(f"  Max Drawdown:     {result.max_drawdown:.2%}")
    print(f"  Calmar Ratio:     {result.calmar_ratio:.3f}")
    print(f"  Win Rate:         {result.win_rate:.1%}")
    print(f"  Profit Factor:    {result.profit_factor:.2f}")
    print(f"  Trades:           {result.trades}")
    print(f"  Final Equity:     ${result.equity_curve.iloc[-1]:,.2f}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
