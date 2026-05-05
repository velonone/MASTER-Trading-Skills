"""
Example: Order Book Imbalance Signal
=====================================
Run: python -m skills.signals.technical.examples.obi_basic
"""

from skills.signals.technical.obi import OrderBookImbalance


def main():
    obi = OrderBookImbalance(levels=5, long_threshold=0.25, short_threshold=-0.25)

    # Strong buy pressure — more bid volume than ask volume
    signal = obi.generate(
        symbol="BTC/USDT",
        bids=[[65000, 10.0], [64990, 8.0], [64980, 5.0]],
        asks=[[65010, 1.0], [65020, 2.0], [65030, 1.5]],
    )
    print(f"Action: {signal.action.value}")
    print(f"Confidence: {signal.confidence}")
    print(f"Evidence: {signal.evidence}")

    # Unified interface (Agent dispatch)
    signals = obi.generate_signals(
        {
            "symbol": "BTC/USDT",
            "bids": [[65000, 10.0]],
            "asks": [[65010, 1.0]],
        }
    )
    print(f"Unified: {signals[0].action.value}")


if __name__ == "__main__":
    main()
