"""
Web3 DEX Execution Layer — On-Chain Alpha Delivery
=====================================================
Provides MEV-protected, gas-optimized execution on Ethereum and L2s.

Connectors:
- Uniswap V4 (ERC-6909 + hooks)
- 1inch Aggregator
- Flashbots Protect / MEV Blocker
"""

from skills.execution.web3.dex_executor import Web3DEXExecutor
from skills.execution.web3.mev_protection import MEVProtection

__all__ = [
    "Web3DEXExecutor",
    "MEVProtection",
]
