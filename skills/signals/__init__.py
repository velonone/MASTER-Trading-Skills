"""
Signal Generation Layer — Controlled Exports
=============================================
Only lightweight technical signals are auto-imported.
Advanced math modules (TDA, chaos, adversarial RL, GP) must be imported explicitly.

Usage:
    from skills.signals import OrderBookImbalance, FundingArbitrageSignal
    from skills.signals.topological.tda import TopologicalCrashDetector  # explicit
"""

from skills.signals.technical.obi import OrderBookImbalance
from skills.signals.technical.funding_arb import FundingArbitrageSignal
from skills.signals.technical.kelly import KellyPositionSizer

__all__ = [
    "OrderBookImbalance",
    "FundingArbitrageSignal",
    "KellyPositionSizer",
]
