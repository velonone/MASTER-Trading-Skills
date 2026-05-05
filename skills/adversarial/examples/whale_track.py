"""
Example: Whale Transaction Classification
==========================================
Run: python -m skills.adversarial.examples.whale_track
"""

from skills.adversarial.whale import WhaleTracker


def main():
    # Without API key — classification logic still works
    tracker = WhaleTracker()

    # Accumulation: whale receives large amount
    acc = tracker.classify_whale_transaction(
        from_addr="0xExchange",
        to_addr="0xWhale",
        value_eth=2000.0,
    )
    print(f"Large inflow: {acc}")

    # Distribution: whale sends large amount
    dist = tracker.classify_whale_transaction(
        from_addr="0xWhale",
        to_addr="0xExchange",
        value_eth=5000.0,
    )
    print(f"Large outflow: {dist}")


if __name__ == "__main__":
    main()
