"""
Universal Data Types for MASTER Trading Skills
================================================
All skills emit and consume these standard types to ensure
interoperability across inference, signal generation, risk management,
and execution layers.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# =============================================================================
# Enums
# =============================================================================


class SignalAction(str, Enum):
    """Discrete trading actions emitted by any signal module."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    CLOSE = "CLOSE"
    EMERGENCY_LIQUIDATE = "EMERGENCY_LIQUIDATE"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LIMIT = "STOP_LIMIT"
    STOP_MARKET = "STOP_MARKET"
    TWAP = "TWAP"
    VWAP = "VWAP"
    ICEBERG = "ICEBERG"
    PEGGED = "PEGGED"


class EffectOrder(str, Enum):
    """Temporal resolution for causal-chain effects."""

    IMMEDIATE = "immediate"  # 0–1 hour
    SHORT_TERM = "short_term"  # 1–24 hours
    MEDIUM_TERM = "medium_term"  # 1–7 days
    LONG_TERM = "long_term"  # 1+ weeks


class EventCategory(str, Enum):
    """Taxonomy of market events for inference primitives."""

    WHALE_MOVEMENT = "whale_movement"
    PROTOCOL_CHANGE = "protocol_change"
    GOVERNANCE = "governance"
    LISTING = "listing"
    HACK_EXPLOIT = "hack_exploit"
    REGULATORY = "regulatory"
    MACRO = "macro"
    TECHNICAL = "technical"
    LIQUIDATION_CASCADE = "liquidation_cascade"
    MEV = "mev"


# =============================================================================
# Core Models
# =============================================================================


class Signal(BaseModel):
    """
    Universal signal emitted by every skill in the pack.
    Agents consume this single schema regardless of signal source.
    """

    action: SignalAction
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence")
    strength: float = Field(default=0.5, ge=0.0, le=1.0, description="Signal intensity")
    symbol: str = Field(..., description="Trading pair or asset symbol, e.g. BTC/USDT")
    timeframe: str | None = Field(default=None, description="1m, 5m, 1h, 4h, 1d, etc.")
    source: str = Field(..., description="Skill name that generated the signal")
    primitive: str | None = Field(default=None, description="Named inference primitive used")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Skill-specific payload")
    evidence: list[str] = Field(default_factory=list, description="Human-readable rationale")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expiry: datetime | None = Field(default=None, description="Signal invalidation time")

    @field_validator("confidence", "strength", mode="before")
    @classmethod
    def _clamp_01(cls, v: float) -> float:
        return max(0.0, min(1.0, float(v)))


class MarketData(BaseModel):
    """Normalized market-data snapshot consumed by signals and execution."""

    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    quote_volume: Decimal
    trades: int = 0
    bid: Decimal | None = None
    ask: Decimal | None = None
    bid_volume: Decimal | None = None
    ask_volume: Decimal | None = None
    funding_rate: Decimal | None = None
    open_interest: Decimal | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class Order(BaseModel):
    """Standardized order request."""

    id: str | None = Field(default=None, description="Client-assigned order ID")
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Decimal | None = None
    stop_price: Decimal | None = None
    time_in_force: Literal["GTC", "IOC", "FOK", "PO"] = "GTC"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Position(BaseModel):
    """Normalized position state."""

    symbol: str
    side: Literal["LONG", "SHORT", "FLAT"]
    size: Decimal
    entry_price: Decimal
    margin: Decimal | None = None
    unrealized_pnl: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    leverage: Decimal = Decimal("1")
    liquidation_price: Decimal | None = None
    opened_at: datetime | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class Trade(BaseModel):
    """Fill / execution record."""

    order_id: str
    trade_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    fee: Decimal = Decimal("0")
    fee_asset: str | None = None
    timestamp: datetime


class RiskLimit(BaseModel):
    """Dynamic risk envelope."""

    max_position_size: Decimal
    max_drawdown_pct: float = Field(default=0.15, ge=0.0, le=1.0)
    max_leverage: Decimal = Decimal("10")
    daily_loss_limit: Decimal | None = None
    correlation_threshold: float = 0.95
    max_orders_per_minute: int = 60
    circuit_breaker: bool = True


class ExecutionReport(BaseModel):
    """Post-execution telemetry."""

    order: Order
    status: Literal["PENDING", "OPEN", "PARTIAL", "FILLED", "CANCELLED", "REJECTED", "EXPIRED"]
    fills: list[Trade] = Field(default_factory=list)
    avg_fill_price: Decimal | None = None
    total_filled: Decimal = Decimal("0")
    remaining: Decimal = Decimal("0")
    slippage_bps: int | None = None
    latency_ms: int | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PrimitiveAccuracy(BaseModel):
    """Self-upgrade telemetry for inference primitives."""

    name: str
    category: str
    times_used: int = 0
    times_correct: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    @property
    def accuracy(self) -> float:
        if self.times_used == 0:
            return 0.5
        return self.times_correct / self.times_used


class CausalEffect(BaseModel):
    """A single node in a causal chain."""

    description: str
    order: EffectOrder
    confidence: float = Field(..., ge=0.0, le=1.0)
    affected_assets: list[str] = Field(default_factory=list)
    direction: Literal["bullish", "bearish", "neutral"]
    magnitude: Literal["small", "medium", "large", "extreme"]


class CausalChain(BaseModel):
    """Complete forward-simulation chain from event to equilibrium."""

    event: str
    category: EventCategory
    timestamp: datetime
    effects: list[CausalEffect] = Field(default_factory=list)
    convergence: str = ""
    overall_confidence: float = 0.0
