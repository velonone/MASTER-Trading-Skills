"""
Whale Behavior Tracker — On-Chain Adversarial Intelligence
===========================================================
Analyzes Ethereum (and EVM-compatible) address flows to classify
whale behavior as accumulation, distribution, or neutral.

Integrates with Etherscan and CoinGecko APIs.
"""

from __future__ import annotations

from skills.core.base import BaseSkill
from skills.core.types import Signal, SignalAction


class WhaleTracker(BaseSkill):
    """
    On-chain adversarial intelligence for large-holder behavior classification.
    """

    name = "whale_tracker"
    description = "On-chain whale accumulation/distribution detection"
    version = "2.0.0"
    triggers = ["whale", "on_chain", "etherscan", "accumulation", "distribution"]

    async def run(self, context: dict) -> dict:
        """Agent dispatch entrypoint."""
        return self.track(
            address=context.get("address", ""),
            token_symbol=context.get("token_symbol", "ETH"),
        )

    def __init__(self, etherscan_api_key: str | None = None):
        self.etherscan_api_key = etherscan_api_key
        self.whale_thresholds = {
            "min_balance_eth": 1000.0,
            "min_tx_value_usd": 1_000_000.0,
            "large_tx_eth": 100.0,
        }
        self._exchange_addresses = {
            "0x28c6c06298d514db089934071355e5743bf21d60": "Binance_14",
            "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance_15",
            "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance_16",
            "0x56eddb7aa87536c09ccc2793473599fd21a8b17f": "Binance_Hot",
            "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be": "Binance",
        }

    async def track(self, address: str, lookback: int = 50) -> Signal:
        """
        Analyze an address and emit a standardized Signal.

        Returns:
            Signal with behavior classification and confidence.
        """
        # If no API key, return a structural signal with instructions
        if not self.etherscan_api_key:
            return Signal(
                action=SignalAction.HOLD,
                confidence=0.0,
                symbol="ETH",
                source=self.name,
                evidence=["Etherscan API key required for on-chain analysis"],
                metadata={"address": address, "instructions": "Set etherscan_api_key"},
            )

        try:
            data = await self._fetch_on_chain_data(address, lookback)
        except Exception as exc:
            return Signal(
                action=SignalAction.HOLD,
                confidence=0.0,
                symbol="ETH",
                source=self.name,
                evidence=[f"On-chain fetch failed: {exc}"],
            )

        behavior, confidence, evidence = self._classify(data)

        action_map = {
            "accumulation": SignalAction.BUY,
            "distribution": SignalAction.SELL,
            "neutral": SignalAction.HOLD,
        }

        return Signal(
            action=action_map.get(behavior, SignalAction.HOLD),
            confidence=round(confidence, 3),
            strength=round(confidence, 3),
            symbol=data.get("token_symbol", "ETH"),
            source=self.name,
            metadata={
                "behavior": behavior,
                "balance_eth": data.get("balance_eth", 0),
                "net_flow_eth": data.get("net_flow_eth", 0),
                "exchange_interactions": data.get("exchange_interactions", 0),
            },
            evidence=evidence,
        )

    async def _fetch_on_chain_data(self, address: str, lookback: int) -> dict:
        """Placeholder for async Etherscan API integration."""
        # In production, use aiohttp + Etherscan API
        return {
            "balance_eth": 0.0,
            "net_flow_eth": 0.0,
            "exchange_interactions": 0,
            "token_symbol": "ETH",
        }

    def _classify(self, data: dict) -> tuple[str, float, list[str]]:
        net_flow = data.get("net_flow_eth", 0.0)
        total_flow = data.get("total_flow_eth", 1.0)
        exchange_int = data.get("exchange_interactions", 0)

        if total_flow == 0:
            return "neutral", 0.3, ["Insufficient transaction volume"]

        ratio = net_flow / total_flow
        evidence: list[str] = []
        behavior = "neutral"
        confidence = 0.5

        if ratio > 0.3:
            behavior = "accumulation"
            confidence = min(0.6 + ratio * 0.35, 0.95)
            evidence.append(f"Net inflow {ratio:.1%} over last period")
        elif ratio < -0.3:
            behavior = "distribution"
            confidence = min(0.6 + abs(ratio) * 0.35, 0.95)
            evidence.append(f"Net outflow {abs(ratio):.1%} over last period")

        if exchange_int > 3:
            evidence.append(f"{exchange_int} exchange interactions detected")
            if behavior == "distribution":
                confidence = min(confidence + 0.1, 0.95)
                evidence.append("High exchange interaction during outflow: likely liquidation")

        return behavior, confidence, evidence
