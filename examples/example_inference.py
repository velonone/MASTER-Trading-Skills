#!/usr/bin/env python3
"""
Example: Higher-Order Inference Engine
=======================================
Run with: python examples/example_inference.py
"""

from skills.inference import HigherOrderInferenceEngine
from skills.core.types import EventCategory


def main():
    print("=" * 60)
    print("MASTER Trading — Inference Engine Example")
    print("=" * 60)

    engine = HigherOrderInferenceEngine()

    events = [
        ("Whale deposits 5000 ETH to exchange", EventCategory.WHALE_MOVEMENT),
        ("Protocol hacked for $50M", EventCategory.HACK_EXPLOIT),
        ("Coinbase announces TOKEN listing", EventCategory.LISTING),
        ("DeFi yields fall below treasury rate", EventCategory.PROTOCOL_CHANGE),
    ]

    for event, category in events:
        print(f"\nEvent: {event}")
        pred = engine.generate_prediction(event, category)
        print(f"  Singularity: {pred['is_singularity']} (score: {pred['singularity_score']})")
        print(f"  Convergence: {pred['convergence']}")
        print(f"  Confidence:  {pred['overall_confidence']:.4f}")
        print(f"  Action:      {pred['signal_action']}")
        print(f"  Effects:     {len(pred['causal_chain'])}")
        for effect in pred['causal_chain'][:3]:
            print(f"    - [{effect['order']}] {effect['direction'].upper()}: {effect['description']}")

    # Diagnostics
    print("\n" + "=" * 60)
    print("Engine Diagnostics")
    print("=" * 60)
    diag = engine.diagnostics()
    print(f"Total predictions: {diag['total_predictions']}")
    print(f"Primitives loaded: {diag['primitives_count']}")
    print(f"Primitive accuracy: {diag['primitive_accuracy']}")


if __name__ == "__main__":
    main()
