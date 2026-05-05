"""
Vectorized Backtest Engine — High-Performance Strategy Validation
====================================================================
Simulates strategy execution on historical OHLCV data with realistic
fill modeling, slippage, funding costs, and risk monitoring.

Design targets:
- 1 year of 1m data in <1 second
- Full trade log + equity curve + drawdown series
- Sharpe, Sortino, Calmar, Omega ratios
"""

from backtest.engine import BacktestEngine
from backtest.broker import BrokerSimulator, VolatilitySlippage
from backtest.metrics import BacktestResult, compute_metrics

__all__ = [
    "BacktestEngine",
    "BrokerSimulator",
    "VolatilitySlippage",
    "BacktestResult",
    "compute_metrics",
]
