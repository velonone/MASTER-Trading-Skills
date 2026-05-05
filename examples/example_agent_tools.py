#!/usr/bin/env python3
"""
Example: LLM Agent Tool Export and Dispatch
============================================
Run with: python examples/example_agent_tools.py
"""

import asyncio

from skills.core import registry
from skills.agent import AgentToolAdapter
from skills.adversarial import FOMODetector
from skills.signals import OrderBookImbalance, FundingArbitrageSignal
from decimal import Decimal


async def main():
    print("=" * 60)
    print("MASTER Trading — LLM Agent Tool Example")
    print("=" * 60)

    # Register skills
    registry.register(FOMODetector())
    registry.register(OrderBookImbalance())
    registry.register(FundingArbitrageSignal())

    # Create adapter
    adapter = AgentToolAdapter(registry)

    # Export OpenAI-compatible tools
    tools = adapter.export_openai_tools()
    print(f"\nExported {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool['function']['name']}: {tool['function']['description']}")

    # Simulate LLM dispatch: FOMO detection
    print("\n--- Dispatching fomo_detector ---")
    result = await adapter.dispatch("fomo_detector", {
        "symbol": "BTC/USDT",
        "prices": [50000, 51000, 53000, 55000],
        "volumes": [100, 300, 800, 2000],
    })
    print(f"Result: {result}")

    # Simulate LLM dispatch: Order Book Imbalance
    print("\n--- Dispatching order_book_imbalance ---")
    result = await adapter.dispatch("order_book_imbalance", {
        "symbol": "ETH/USDT",
        "bids": [[3500, 10.0], [3499, 5.0]],
        "asks": [[3501, 2.0], [3502, 8.0]],
    })
    print(f"Result: {result}")

    # Simulate LLM dispatch: Funding Arbitrage
    print("\n--- Dispatching funding_arbitrage ---")
    result = await adapter.dispatch("funding_arbitrage", {
        "symbol": "BTC/USDT",
        "funding_rate": -0.0005,
    })
    print(f"Result: {result}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
