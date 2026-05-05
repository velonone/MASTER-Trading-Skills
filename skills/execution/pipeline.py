"""
TradingPipeline — Minimal Signal → Risk → OMS → Connector Orchestrator
=======================================================================

Closes the canonical execution loop in roughly 100 lines:

    pipeline = TradingPipeline(
        strategy=my_strategy,
        risk=DynamicRiskManager(),
        oms=OrderManagementSystem(),
        connector=ccxt_connector,
        sizer=fixed_qty_sizer,
    )
    report = await pipeline.process(market_data, position=current_position)

Each :class:`TradingPipeline.process` call performs:

    1. ``strategy.generate_signals(context)`` → ``List[Signal]``
    2. ``risk.evaluate_signal(signal, position)`` → possibly downgraded
    3. ``oms.signal_to_order(signal, qty)`` → ``Order``
    4. ``risk.evaluate_order(order)`` → modified or ``None``
    5. ``connector.place_order(order)`` → ``ExecutionReport``
    6. ``oms.on_report(report)`` and ``risk.on_fill(report)``

The pipeline does **not** start its own loop, fetch market data, or schedule
itself — those concerns belong to the user (cron, async loop, websocket
handler, etc.). It is the *seam* that wires the existing components into a
single auditable call.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from skills.core.base import BaseConnector, BaseRiskManager, BaseStrategy
from skills.core.logging import get_logger
from skills.core.types import (
    ExecutionReport,
    Order,
    Position,
    Signal,
    SignalAction,
)
from skills.execution.oms import OrderManagementSystem

_logger = get_logger("pipeline")


SizerFn = Callable[[Signal, Position | None], Decimal]
"""Callable that returns the order quantity for a given signal/position."""


@dataclass
class PipelineStep:
    """One full pass through the pipeline. Useful for tests and audits."""

    signal: Signal
    risk_signal: Signal | None = None
    order: Order | None = None
    risked_order: Order | None = None
    report: ExecutionReport | None = None
    rejected_reason: str | None = None


@dataclass
class PipelineResult:
    """Aggregated outcome of one ``process()`` invocation."""

    steps: list[PipelineStep] = field(default_factory=list)

    @property
    def reports(self) -> list[ExecutionReport]:
        return [s.report for s in self.steps if s.report is not None]


def fixed_qty_sizer(qty: Decimal) -> SizerFn:
    """Trivial sizer that always returns ``qty``."""

    def _size(_signal: Signal, _position: Position | None) -> Decimal:
        return qty

    return _size


class TradingPipeline:
    """
    Compose strategy + risk + OMS + connector into a single ``process`` call.

    The pipeline owns no market-data feed and no scheduling — the caller
    drives it (one call per bar, per tick, per signal batch, etc.).
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        risk: BaseRiskManager,
        oms: OrderManagementSystem,
        connector: BaseConnector,
        sizer: SizerFn,
        order_type: str = "MARKET",
    ):
        self.strategy = strategy
        self.risk = risk
        self.oms = oms
        self.connector = connector
        self.sizer = sizer
        self.order_type = order_type

    async def process(
        self,
        context: dict[str, Any],
        position: Position | None = None,
    ) -> PipelineResult:
        """
        Run one strategy → risk → OMS → connector pass.

        ``context`` is forwarded to the strategy (typically a bar dict or a
        normalized market snapshot). ``position`` is the current authoritative
        position used for risk gating; pass ``None`` for fresh starts and the
        pipeline will fall back to the OMS-tracked position.
        """
        result = PipelineResult()
        signals: list[Signal] = list(self.strategy.generate_signals(context))

        for signal in signals:
            step = PipelineStep(signal=signal)
            result.steps.append(step)

            if signal.action == SignalAction.HOLD:
                step.rejected_reason = "HOLD"
                continue

            current_pos = position or self.oms.position(signal.symbol)
            risked_signal = await self.risk.evaluate_signal(signal, current_pos)
            step.risk_signal = risked_signal

            if risked_signal.action == SignalAction.HOLD:
                step.rejected_reason = "RISK_BLOCKED_SIGNAL"
                _logger.info(
                    "pipeline.signal_blocked symbol=%s reason=%s",
                    signal.symbol,
                    risked_signal.evidence,
                )
                continue

            qty = self.sizer(risked_signal, current_pos)
            if qty <= 0:
                step.rejected_reason = "SIZER_RETURNED_NON_POSITIVE"
                continue

            order = self.oms.signal_to_order(risked_signal, qty=qty, order_type=self.order_type)
            step.order = order
            await self.oms.submit(order)

            risked_order = await self.risk.evaluate_order(order)
            step.risked_order = risked_order

            if risked_order is None:
                step.rejected_reason = "RISK_BLOCKED_ORDER"
                _logger.info("pipeline.order_blocked symbol=%s", order.symbol)
                continue

            report = await self.connector.place_order(risked_order)
            step.report = report
            await self.oms.on_report(report)
            await self.risk.on_fill(report)

        return result
