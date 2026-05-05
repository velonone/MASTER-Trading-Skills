"""
Execution Layer — Controlled Exports
=====================================
Only core execution abstractions are auto-imported.
Venue-specific connectors (CCXT, Web3) must be imported explicitly.

Usage:
    from skills.execution import DynamicRiskManager, OrderManagementSystem
    from skills.execution.connectors.ccxt_connector import CCXTConnector  # explicit
    from skills.execution.web3.dex_executor import Web3DEXExecutor       # explicit
"""

from skills.execution.oms import OrderManagementSystem
from skills.execution.pipeline import (
    PipelineResult,
    PipelineStep,
    TradingPipeline,
    fixed_qty_sizer,
)
from skills.execution.risk import DynamicRiskManager

__all__ = [
    "DynamicRiskManager",
    "OrderManagementSystem",
    "TradingPipeline",
    "PipelineResult",
    "PipelineStep",
    "fixed_qty_sizer",
]
