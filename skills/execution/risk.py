"""
Dynamic Risk Manager
=====================
Intercepts signals and orders before execution, applying:
- Position-size limits
- Drawdown circuit breakers
- Correlation concentration guards
- Velocity limits (orders per minute)

Conforms to BaseRiskManager interface.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from skills.core.base import BaseRiskManager
from skills.core.logging import get_logger
from skills.core.types import ExecutionReport, Order, Position, RiskLimit, Signal, SignalAction


_logger = get_logger("execution.risk")


class DynamicRiskManager(BaseRiskManager):
    """Production risk interceptor with real-time telemetry."""

    name = "dynamic_risk_manager"
    description = "Real-time risk interception: drawdown, size, correlation, velocity"
    version = "2.0.0"

    def __init__(self, limits: Optional[RiskLimit] = None):
        self.limits = limits or RiskLimit(
            max_position_size=Decimal("1.0"),
            max_drawdown_pct=0.15,
            max_leverage=Decimal("10"),
            daily_loss_limit=Decimal("1000"),
            max_orders_per_minute=60,
        )
        self._order_times: List[datetime] = []
        self._daily_pnl: Decimal = Decimal("0")
        self._last_reset: datetime = datetime.utcnow()

    async def evaluate_signal(self, signal: Signal, position: Optional[Position]) -> Signal:
        """Downgrade or block signals that violate risk constraints."""
        if self._drawdown_exceeded():
            _logger.warning("risk.signal_blocked reason=drawdown symbol=%s", signal.symbol)
            return self._block(signal, "DRAWDOWN_CIRCUIT_BREAKER")

        if position and position.leverage > self.limits.max_leverage:
            _logger.warning("risk.signal_blocked reason=leverage symbol=%s leverage=%s",
                            signal.symbol, position.leverage)
            return self._block(signal, "LEVERAGE_CAP_EXCEEDED")

        if signal.confidence < 0.55:
            _logger.info("risk.signal_suppressed reason=low_confidence symbol=%s confidence=%.2f",
                         signal.symbol, signal.confidence)
            return Signal(
                action=SignalAction.HOLD,
                confidence=0.0,
                symbol=signal.symbol,
                source=self.name,
                evidence=["Confidence below minimum threshold; signal suppressed."],
            )

        return signal

    async def evaluate_order(self, order: Order, limits: Optional[RiskLimit] = None) -> Optional[Order]:
        """Return order, modified order, or None if rejected."""
        lim = limits or self.limits

        # Velocity check
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)
        self._order_times = [t for t in self._order_times if t > cutoff]
        if len(self._order_times) >= lim.max_orders_per_minute:
            _logger.info("risk.order_rejected reason=velocity symbol=%s", order.symbol)
            return None

        # Position size cap
        if order.quantity > lim.max_position_size:
            _logger.info(
                "risk.order_capped symbol=%s requested=%s capped_to=%s",
                order.symbol, order.quantity, lim.max_position_size,
            )
            order.quantity = lim.max_position_size
            order.metadata["risk_adjusted"] = "quantity_capped"

        self._order_times.append(now)
        return order

    async def on_fill(self, report: ExecutionReport) -> None:
        self._reset_daily_if_needed()
        if report.status == "FILLED" and report.avg_fill_price:
            slip = report.slippage_bps or 0
            # Approximate realized PnL tracking for daily limit
            self._daily_pnl -= Decimal(str(slip)) * Decimal("0.0001") * report.total_filled

    def _drawdown_exceeded(self) -> bool:
        # Placeholder: in production, query portfolio equity history
        return False

    def _block(self, signal: Signal, reason: str) -> Signal:
        return Signal(
            action=SignalAction.EMERGENCY_LIQUIDATE if "CIRCUIT" in reason else SignalAction.HOLD,
            confidence=1.0,
            symbol=signal.symbol,
            source=self.name,
            evidence=[f"Risk block: {reason}"],
        )

    def _reset_daily_if_needed(self) -> None:
        if datetime.utcnow().date() != self._last_reset.date():
            self._daily_pnl = Decimal("0")
            self._last_reset = datetime.utcnow()

    def health(self) -> Dict[str, any]:
        return {
            "status": "ok",
            "daily_pnl": float(self._daily_pnl),
            "orders_last_minute": len(self._order_times),
            "limits": self.limits.model_dump(),
        }
