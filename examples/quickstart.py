"""
master-trading-skills · 60-second quickstart
=============================================

Run after `pip install -e ".[dev]"`:

    python examples/quickstart.py

This script exercises the typed surface end to end without touching any
network — everything is in-memory:

  1. Resolve calibration (bundled VelonLabs Reference Snapshot v2026.05).
  2. Build a higher-order inference engine and ask it to reason about a
     whale-deposit event. Verify the output carries provenance metadata.
  3. Wire up an Agent policy gate (read+signal only, no trading) and
     confirm a trade-tier dispatch is rejected.
  4. Run a one-bar synthetic backtest through the vectorised engine.

If everything prints "ok", your install is healthy.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

from skills.agent import AgentPolicy, AgentToolAdapter
from skills.core.registry import SkillRegistry
from skills.core.types import EventCategory, ExecutionReport, Order, OrderSide, Position
from skills.core.base import BaseConnector
from skills.inference import HigherOrderInferenceEngine


# ────────────────────────── 1. Inference + provenance ──────────────────────────

def run_inference():
    print("─── 1. Higher-order inference ─────────────────────────────────")
    engine = HigherOrderInferenceEngine()
    pred = engine.generate_prediction(
        "Whale 0xabc deposited 5000 ETH to Binance",
        EventCategory.WHALE_MOVEMENT,
    )

    meta = pred["_meta"]
    print(f"  signal_action      : {pred['signal_action']}")
    print(f"  overall_confidence : {pred['overall_confidence']}")
    print(f"  calibration_source : {meta['calibration_source']}")
    print(f"  calibration_version: {meta['calibration_version']}")
    print(f"  attribution        : {meta['attribution']}")

    assert meta["calibration_source"] == "snapshot", "expected bundled snapshot"
    assert meta["attribution"] == "VelonLabs Reference Calibration"
    print("  ok — every prediction carries auditable provenance.\n")


# ────────────────────────── 2. Agent policy gate ──────────────────────────

class _FakeTradeConnector(BaseConnector):
    """Test double — pretends to be an exchange so we can exercise the gate."""

    name = "fake_trade_connector"
    description = "test trade connector"
    venue = "test"

    async def fetch_ohlcv(self, symbol, timeframe="1h", limit=100):
        return []

    async def place_order(self, order: Order) -> ExecutionReport:
        return ExecutionReport(order=order, status="FILLED", total_filled=order.quantity)

    async def cancel_order(self, order_id: str, symbol: str) -> ExecutionReport:
        return ExecutionReport(
            order=Order(
                symbol=symbol, side=OrderSide.SELL, order_type="MARKET", quantity=Decimal("0")
            ),
            status="CANCELLED",
        )

    async def fetch_position(self, symbol: str) -> Position | None:
        return None

    async def run(self, context):
        return {"executed": True}


async def run_policy_gate():
    print("─── 2. Agent policy gate ──────────────────────────────────────")
    registry = SkillRegistry()
    registry.register(_FakeTradeConnector())

    # Read-only policy — no trade capability.
    policy = AgentPolicy.read_only()
    adapter = AgentToolAdapter(registry, policy=policy)

    result = await adapter.dispatch("fake_trade_connector", {"context": {"amount_in": 10}})
    print(f"  status = {result['status']}")
    print(f"  code   = {result['code']}")
    print(f"  reason = {result['message']}")

    assert result["status"] == "error"
    assert result["code"] == "POLICY_DENIED"
    print("  ok — read-only policy blocked the trade-tier dispatch.\n")


# ────────────────────────── 3. Backtest one-bar smoke ──────────────────────────

def run_backtest():
    print("─── 3. Backtest engine smoke ──────────────────────────────────")

    import pandas as pd

    from backtest import BacktestEngine
    from skills.core.types import Signal, SignalAction

    df = pd.DataFrame(
        {
            "open":   [100, 101, 102, 103, 104],
            "high":   [101, 102, 103, 104, 105],
            "low":    [99,  100, 101, 102, 103],
            "close":  [101, 102, 103, 104, 105],
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
                    symbol="DEMO",
                    source="quickstart",
                )
            ]

    engine = BacktestEngine(data=df, strategy=AlwaysBuy(), initial_capital=10_000)
    result = engine.run()

    print(f"  trades        = {result.trades}")
    print(f"  total_return  = {result.total_return:.4f}")
    print(f"  sharpe_ratio  = {result.sharpe_ratio:.4f}")
    print(f"  max_drawdown  = {result.max_drawdown:.4f}")

    assert result.total_return > 0, "rising market AlwaysBuy should profit"
    print("  ok — vectorised backtest engine produced sane metrics.\n")


# ────────────────────────── orchestration ──────────────────────────

def main():
    run_inference()
    asyncio.run(run_policy_gate())
    run_backtest()
    print("All quickstart steps passed.")
    print()
    print("Next: read SKILL.md for the full tool inventory, or look at")
    print("examples/example_inference.py / example_backtest.py / example_agent_tools.py")
    print("for deeper walk-throughs.")


if __name__ == "__main__":
    main()
