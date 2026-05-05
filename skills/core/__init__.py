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

from skills.core.types import (
    Signal,
    SignalAction,
    Position,
    Order,
    OrderType,
    OrderSide,
    Trade,
    MarketData,
    RiskLimit,
    ExecutionReport,
    PrimitiveAccuracy,
)
from skills.core.base import (
    BaseStrategy,
    BaseRiskManager,
    BaseConnector,
    BaseSkill,
)
from skills.core.registry import SkillRegistry, registry

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
