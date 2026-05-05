"""
Abstract Base Classes for MASTER Trading Skills
=================================================
Every skill in the pack inherits from one of these bases,
ensuring a uniform interface for the Agent runtime.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from skills.core.types import (
    ExecutionReport,
    MarketData,
    Order,
    Position,
    RiskLimit,
    Signal,
)


class BaseSkill(ABC):
    """
    Minimal contract for any skill loadable by the SkillRegistry.
    """
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    triggers: List[str] = []

    async def start(self) -> None:
        """Lifecycle hook called before the skill begins serving requests."""
        pass

    async def stop(self) -> None:
        """Lifecycle hook called when the skill is being shut down."""
        pass

    def health(self) -> Dict[str, Any]:
        """Return health status for observability."""
        return {"status": "ok", "skill": self.name, "version": self.version}

    @abstractmethod
    async def run(self, context: Dict[str, Any]) -> Any:
        """Execute the skill with the provided context."""
        ...


class BaseStrategy(BaseSkill):
    """
    Base for all signal-generation strategies.
    Emits standardized Signal objects from context.
    """
    name: str = "base_strategy"
    supported_timeframes: List[str] = ["1h", "4h", "1d"]

    async def run(self, context: Dict[str, Any]) -> Any:
        """Default agent dispatch runner — delegates to generate_signals()."""
        return self.generate_signals(context)

    @abstractmethod
    def generate_signals(self, context: Dict[str, Any]) -> List[Signal]:
        """Generate signals from a context dict."""
        ...

    async def warmup(self, data: List[MarketData]) -> None:
        """Optional warmup / state initialization (e.g. indicators)."""
        pass


class BaseRiskManager(BaseSkill):
    """
    Base for risk-management modules.
    Intercepts signals and orders before execution.
    """
    name: str = "base_risk_manager"

    async def run(self, context: Dict[str, Any]) -> Any:
        """Default agent dispatch runner. Routes to evaluate_signal or evaluate_order."""
        if "signal" in context:
            result = await self.evaluate_signal(context["signal"], context.get("position"))
            return {"result": result, "type": "signal_evaluation"}
        if "order" in context:
            result = await self.evaluate_order(context["order"], context.get("limits"))
            return {"result": result, "type": "order_evaluation"}
        return {"error": "No signal or order in context"}

    @abstractmethod
    async def evaluate_signal(self, signal: Signal, position: Optional[Position]) -> Signal:
        """
        Return the signal unchanged, modified, or flatted to HOLD
        based on risk constraints.
        """
        ...

    @abstractmethod
    async def evaluate_order(self, order: Order, limits: Optional[RiskLimit] = None) -> Optional[Order]:
        """Return the order, a modified order, or None if rejected."""
        ...

    async def on_fill(self, report: ExecutionReport) -> None:
        """Hook called after every execution for PnL / drawdown tracking."""
        pass


class BaseConnector(BaseSkill):
    """
    Base for exchange / DEX connectors.
    Normalizes every venue into the same MarketData / Order / Trade schema.
    """
    name: str = "base_connector"
    venue: str = ""

    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[MarketData]:
        ...

    @abstractmethod
    async def place_order(self, order: Order) -> ExecutionReport:
        ...

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> ExecutionReport:
        ...

    @abstractmethod
    async def fetch_position(self, symbol: str) -> Optional[Position]:
        ...

    async def stream_ticks(self, symbol: str):
        """Async generator for real-time tick data (optional)."""
        raise NotImplementedError("Streaming not supported by this connector")
