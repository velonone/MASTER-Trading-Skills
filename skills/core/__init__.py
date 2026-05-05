"""
MASTER Trading — Core Abstraction Layer
========================================
Provides universal types, base classes, and the skill registry
used across all trading signal, inference, and execution modules.

Design Principles:
- Zero-dependency between skills (loosely coupled via registry)
- All public APIs are typed (Pydantic v2 + Python 3.11+)
- Every signal carries provenance (which skill, confidence, timestamp)
"""

from skills.core.base import (
    BaseConnector,
    BaseRiskManager,
    BaseSkill,
    BaseStrategy,
)
from skills.core.registry import SkillRegistry, registry
from skills.core.types import (
    ExecutionReport,
    MarketData,
    Order,
    OrderSide,
    OrderType,
    Position,
    PrimitiveAccuracy,
    RiskLimit,
    Signal,
    SignalAction,
    Trade,
)

__all__ = [
    # Types
    "Signal",
    "SignalAction",
    "Position",
    "Order",
    "OrderType",
    "OrderSide",
    "Trade",
    "MarketData",
    "RiskLimit",
    "ExecutionReport",
    "PrimitiveAccuracy",
    # Bases
    "BaseStrategy",
    "BaseRiskManager",
    "BaseConnector",
    "BaseSkill",
    # Registry
    "SkillRegistry",
    "registry",
]
