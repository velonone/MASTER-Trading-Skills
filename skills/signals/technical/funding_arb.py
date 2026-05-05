"""
Funding Rate Arbitrage Signal
==============================
Detects dislocations between perpetual funding rates and spot prices,
suggesting basis-trading opportunities.

Threshold default: ±0.03% (30 bps) per 8h interval ≈ 32.85% annualized.
"""

from decimal import Decimal
from skills.core.base import BaseStrategy
from skills.core.types import Signal, SignalAction


class FundingArbitrageSignal(BaseStrategy):
    """Generates signals from funding rate extremes."""

    name = "funding_arbitrage"
    description = "Basis-trading signal from perpetual funding rate dislocation"
    version = "1.0.0"
    triggers = ["funding", "perpetual", "basis", "arbitrage"]

    def __init__(self, threshold: Decimal = Decimal("0.0003")):
        self.threshold = threshold

    def generate_signals(self, context: dict) -> list:
        """Unified interface -- delegates to generate()."""
        from decimal import Decimal
        return [self.generate(
            symbol=context.get("symbol", "BTC/USDT"),
            funding_rate=Decimal(str(context.get("funding_rate", 0))),
            annualized_estimate=Decimal(str(context.get("annualized_estimate", 0))) if context.get("annualized_estimate") else None,
        )]

    async def run(self, context: dict) -> Signal:
        """Agent dispatch entrypoint."""
        signals = self.generate_signals(context)
        return signals[0] if signals else Signal(
            action=SignalAction.HOLD,
            confidence=0.0,
            strength=0.0,
            symbol=context.get("symbol", "BTC/USDT"),
            source=self.name,
            evidence=["No signal generated"],
        )

    def generate(self, symbol: str, funding_rate: Decimal, annualized_estimate: Decimal | None = None) -> Signal:
        """
        Args:
            funding_rate: Current 8h funding rate (e.g. 0.0003 = 0.03%).
            annualized_estimate: Optional pre-computed annualized rate.
        """
        fr = float(funding_rate)
        th = float(self.threshold)

        if fr > th:
            action = SignalAction.SELL
            evidence = f"Funding rate {fr:.4%} > threshold {th:.4%}; short perp + long spot"
        elif fr < -th:
            action = SignalAction.BUY
            evidence = f"Funding rate {fr:.4%} < -threshold {-th:.4%}; long perp + short spot"
        else:
            action = SignalAction.HOLD
            evidence = f"Funding rate {fr:.4%} within neutral band ±{th:.4%}"

        strength = min(abs(fr) / (th * 3), 1.0)  # 3x threshold = max strength

        return Signal(
            action=action,
            confidence=round(0.5 + 0.4 * strength, 3),
            strength=round(strength, 3),
            symbol=symbol,
            source=self.name,
            metadata={
                "funding_rate_8h": fr,
                "threshold": th,
                "annualized_estimate": float(annualized_estimate) if annualized_estimate else fr * 3 * 365,
            },
            evidence=[evidence],
        )
