"""
Vectorized Backtest Engine
============================
High-performance bar-by-bar strategy simulation.

Usage:
    engine = BacktestEngine(data=df, strategy=my_strategy, initial_capital=100_000)
    result = engine.run()
    print(result.sharpe_ratio, result.max_drawdown)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from backtest.broker import BrokerSimulator, FillResult
from backtest.metrics import BacktestResult, compute_metrics
from skills.core.types import OrderSide, Signal, SignalAction  # noqa: F401


class BacktestEngine:
    """
    Production-grade vectorized backtest engine.
    Supports multi-asset, multi-strategy, and fractional position sizing.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        strategy: Any,
        initial_capital: float = 100_000.0,
        commission: float = 0.0004,
        slippage_model=None,
        allow_short: bool = True,
        funding_interval: str = "8h",
    ):
        """
        Args:
            data: DataFrame with columns [open, high, low, close, volume] indexed by datetime.
            strategy: Object with `generate(signal_data) -> List[Signal]` method.
            initial_capital: Starting capital in quote currency.
            commission: Commission rate per trade (e.g. 0.0004 = 4 bps).
            slippage_model: SlippageModel instance.
            allow_short: Whether short selling is permitted.
            funding_interval: Perpetual funding interval for cost simulation.
        """
        self.data = data.copy()
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.broker = BrokerSimulator(
            slippage_model=slippage_model,
            commission_rate=commission,
            allow_short=allow_short,
        )
        self.allow_short = allow_short
        self.funding_interval = funding_interval

        # State
        self.capital = initial_capital
        self.position: float = 0.0  # units of base asset
        self.equity_curve: List[float] = []
        self.trade_log: List[Dict[str, Any]] = []
        self._entry_price: Optional[float] = None

    def run(self) -> BacktestResult:
        """
        Execute bar-by-bar backtest with strict next-bar fill ordering.

        Each iteration:
          1. Execute pending signals (from prior bar) against the current bar.
             The broker fills at the current bar's open, so the strategy
             cannot peek at the bar that produces its fill.
          2. Mark-to-market against the current bar's close.
          3. Run the strategy on the current bar; resulting signals become
             pending for the next bar.

        Signals generated on the final bar never execute (no next-bar to
        fill against), which is the correct lookahead-free behavior.
        """
        df = self.data.reset_index()
        if "timestamp" not in df.columns and "index" in df.columns:
            df.rename(columns={"index": "timestamp"}, inplace=True)

        pending_signals: List[Signal] = []
        for _, row in df.iterrows():
            bar = row.to_dict()

            # Step 1: fill prior-bar signals at this bar's open.
            for signal in pending_signals:
                self._process_signal(signal, bar)
            pending_signals = []

            # Step 2: mark-to-market on this bar's close.
            price = bar["close"]
            equity = self.capital + self.position * price
            self.equity_curve.append(equity)

            # Step 3: generate next-bar signals from this bar.
            if hasattr(self.strategy, "generate_signals"):
                pending_signals = list(self.strategy.generate_signals(bar))
            else:
                pending_signals = list(self.strategy.generate(bar))

        equity_series = pd.Series(self.equity_curve, index=self.data.index[: len(self.equity_curve)])
        return compute_metrics(equity_series, self.trade_log)

    def _process_signal(self, signal: Signal, bar: dict) -> None:
        """
        Convert signal to simulated fill at the start of *bar*.

        Sizing uses ``bar["open"]`` — the only price known at fill time.
        Using close here would be a lookahead (the close is determined
        after the fill).
        """
        if signal.action == SignalAction.HOLD:
            return

        price = bar["open"]
        target_position = self._target_position(signal, price)
        delta = target_position - self.position

        if abs(delta) < 1e-9:
            return

        side = "buy" if delta > 0 else "sell"
        fill = self.broker.simulate_market_order(abs(delta), bar, side)

        if side == "buy":
            cost = fill.price * fill.quantity + fill.fee
            self.capital -= cost
            self.position += fill.quantity
        else:
            proceeds = fill.price * fill.quantity - fill.fee
            self.capital += proceeds
            self.position -= fill.quantity

        pnl = 0.0
        if self._entry_price is not None and self.position == 0:
            pnl = (fill.price - self._entry_price) * fill.quantity * (1 if side == "sell" else -1)
            self._entry_price = None
        elif self.position != 0 and self._entry_price is None:
            self._entry_price = fill.price

        self.trade_log.append({
            "timestamp": bar.get("timestamp", ""),
            "side": side,
            "price": fill.price,
            "quantity": fill.quantity,
            "slippage_bps": fill.slippage_bps,
            "fee": fill.fee,
            "pnl": pnl,
            "capital": self.capital,
            "position": self.position,
        })

    def _target_position(self, signal: Signal, price: float) -> float:
        """Map signal to target position size."""
        if signal.action == SignalAction.BUY:
            # Allocate signal.strength * 100% of capital
            notional = self.capital * signal.strength
            return notional / price if price > 0 else 0.0
        if signal.action == SignalAction.SELL:
            if not self.allow_short:
                return 0.0
            notional = self.capital * signal.strength
            return -notional / price if price > 0 else 0.0
        if signal.action == SignalAction.CLOSE:
            return 0.0
        return self.position
