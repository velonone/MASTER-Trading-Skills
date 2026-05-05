"""
Backtest Performance Metrics
=============================
Computes institutional-grade risk-adjusted performance metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    """Container for backtest outputs."""

    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    total_return: float = 0.0
    annualized_return: float = 0.0
    annualized_volatility: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_trade_pnl: float = 0.0
    trades: int = 0
    equity_curve: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    drawdown_series: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    trade_log: list[dict] = field(default_factory=list)


def compute_metrics(
    equity_curve: pd.Series, trade_log: list[dict], risk_free_rate: float = 0.0
) -> BacktestResult:
    """Compute full metrics from an equity curve and trade log."""
    returns = equity_curve.pct_change().dropna()
    if len(returns) == 0 or returns.std() == 0:
        return BacktestResult(equity_curve=equity_curve)

    # Basic return metrics
    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1.0
    n_years = len(returns) / 365.0  # assume daily; caller should scale
    annualized_return = (1 + total_return) ** (1 / max(n_years, 1e-6)) - 1.0
    annualized_vol = returns.std() * np.sqrt(365)

    # Sharpe
    excess = returns - risk_free_rate / 365
    sharpe = (excess.mean() / excess.std()) * np.sqrt(365) if excess.std() > 0 else 0.0

    # Sortino (downside deviation)
    downside = returns[returns < 0]
    downside_std = downside.std() * np.sqrt(365) if len(downside) > 0 else 1e-10
    sortino = (returns.mean() * 365 - risk_free_rate) / downside_std

    # Drawdown
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak
    max_dd = drawdown.min()
    max_dd_duration = _max_drawdown_duration(drawdown)

    # Calmar
    calmar = annualized_return / abs(max_dd) if max_dd != 0 else 0.0

    # Trade metrics
    pnls = [t.get("pnl", 0.0) for t in trade_log]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    win_rate = len(wins) / len(pnls) if pnls else 0.0
    profit_factor = sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else float("inf")
    avg_pnl = np.mean(pnls) if pnls else 0.0

    return BacktestResult(
        sharpe_ratio=round(sharpe, 4),
        sortino_ratio=round(sortino, 4),
        calmar_ratio=round(calmar, 4),
        max_drawdown=round(max_dd, 4),
        max_drawdown_duration=max_dd_duration,
        total_return=round(total_return, 4),
        annualized_return=round(annualized_return, 4),
        annualized_volatility=round(annualized_vol, 4),
        win_rate=round(win_rate, 4),
        profit_factor=round(profit_factor, 4),
        avg_trade_pnl=round(avg_pnl, 4),
        trades=len(trade_log),
        equity_curve=equity_curve,
        drawdown_series=drawdown,
        trade_log=trade_log,
    )


def _max_drawdown_duration(drawdown: pd.Series) -> int:
    """Compute longest drawdown duration in periods."""
    in_drawdown = drawdown < 0
    if not in_drawdown.any():
        return 0
    # Find runs of True
    groups = (in_drawdown != in_drawdown.shift()).cumsum()
    durations = in_drawdown.groupby(groups).sum()
    return int(durations.max())
