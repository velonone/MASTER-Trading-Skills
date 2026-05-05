"""
Example: Funding Arbitrage Signal
==================================
Run: python -m skills.signals.technical.examples.funding_arb_basic
"""
from decimal import Decimal
from skills.signals.technical.funding_arb import FundingArbitrageSignal


def main():
    fa = FundingArbitrageSignal(threshold=Decimal("0.0003"))

    # Positive funding rate → short perp + long spot
    signal = fa.generate(
        symbol="BTC/USDT",
        funding_rate=Decimal("0.0005"),
    )
    print(f"Action: {signal.action.value}")
    print(f"Confidence: {signal.confidence}")
    print(f"Evidence: {signal.evidence}")

    # Negative funding rate → long perp + short spot
    signal2 = fa.generate(
        symbol="BTC/USDT",
        funding_rate=Decimal("-0.0006"),
    )
    print(f"Action (negative): {signal2.action.value}")


if __name__ == "__main__":
    main()
