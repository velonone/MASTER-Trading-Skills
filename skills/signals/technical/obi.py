"""
Order Book Imbalance (OBI) — Market Microstructure Signal
==========================================================
Measures the asymmetry between bid and ask depth at the top-N levels.
Positive OBI → buying pressure; Negative OBI → selling pressure.

Reference: Stoikov (2018), "The Micro-Price: A High Frequency Estimator"
"""

from skills.core.base import BaseStrategy
from skills.core.types import Signal, SignalAction


def calculate_obi(
    bids: list[tuple[float, float]], asks: list[tuple[float, float]], levels: int = 5
) -> float:
    """
    Compute Order Book Imbalance for top-N levels.

    Args:
        bids: List of (price, volume) tuples sorted descending by price.
        asks: List of (price, volume) tuples sorted ascending by price.
        levels: Number of price levels to aggregate.

    Returns:
        OBI in range [-1, 1]. Positive = bid-heavy.
    """
    bid_vol = sum(b[1] for b in bids[:levels])
    ask_vol = sum(a[1] for a in asks[:levels])
    total = bid_vol + ask_vol
    if total == 0:
        return 0.0
    return (bid_vol - ask_vol) / total


class OrderBookImbalance(BaseStrategy):
    """Stateful OBI signal generator with threshold-based action mapping."""

    name = "order_book_imbalance"
    description = "Generates trading signals from top-of-book depth asymmetry"
    version = "1.0.0"
    triggers = ["order_book", "obi", "depth", "microstructure"]

    def __init__(
        self, levels: int = 5, long_threshold: float = 0.25, short_threshold: float = -0.25
    ):
        self.levels = levels
        self.long_threshold = long_threshold
        self.short_threshold = short_threshold

    def generate_signals(self, context: dict) -> list:
        """Unified interface -- delegates to generate()."""
        return [
            self.generate(
                symbol=context.get("symbol", "BTC/USDT"),
                bids=context.get("bids", []),
                asks=context.get("asks", []),
            )
        ]

    async def run(self, context: dict) -> Signal:
        """Agent dispatch entrypoint."""
        signals = self.generate_signals(context)
        return (
            signals[0]
            if signals
            else Signal(
                action=SignalAction.HOLD,
                confidence=0.0,
                strength=0.0,
                symbol=context.get("symbol", "BTC/USDT"),
                source=self.name,
                evidence=["No signal generated"],
            )
        )

    def generate(
        self, symbol: str, bids: list[tuple[float, float]], asks: list[tuple[float, float]]
    ) -> Signal:
        obi = calculate_obi(bids, asks, self.levels)

        if obi >= self.long_threshold:
            action = SignalAction.BUY
        elif obi <= self.short_threshold:
            action = SignalAction.SELL
        else:
            action = SignalAction.HOLD

        # Map |obi| to strength [0,1]
        strength = min(abs(obi), 1.0)

        return Signal(
            action=action,
            confidence=round(0.5 + 0.5 * strength, 3),
            strength=round(strength, 3),
            symbol=symbol,
            source=self.name,
            metadata={"obi": round(obi, 4), "levels": self.levels},
            evidence=[f"OBI={obi:+.4f} at top-{self.levels} levels"],
        )
