"""
MEV Protection Layer
=====================
Routes transactions through private mempools to prevent
sandwich attacks and front-running.

Supported relays:
- Flashbots Protect (default)
- MEV Blocker (CowSwap)
- Eden Network
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class MEVProtection:
    """Configuration and RPC endpoint management for MEV protection."""

    RELAYS = {
        "flashbots": {
            "rpc": "https://rpc.flashbots.net/fast",
            "description": "Flashbots Protect with fast inclusion",
        },
        "flashbots_standard": {
            "rpc": "https://rpc.flashbots.net",
            "description": "Flashbots Protect standard (max privacy)",
        },
        "mevblocker": {
            "rpc": "https://rpc.mevblocker.io",
            "description": "MEV Blocker by CowSwap",
        },
        "eden": {
            "rpc": "https://api.edennetwork.io/v1/rpc",
            "description": "Eden Network RPC",
        },
    }

    def __init__(self, provider: str = "flashbots"):
        if provider not in self.RELAYS:
            raise ValueError(f"Unknown MEV provider: {provider}. Choose from {list(self.RELAYS.keys())}")
        self.provider = provider
        self.rpc_url = self.RELAYS[provider]["rpc"]

    def headers(self) -> Dict[str, str]:
        """Optional headers for RPC authentication."""
        return {"Content-Type": "application/json"}

    def __repr__(self) -> str:
        return f"<MEVProtection provider={self.provider}>"
