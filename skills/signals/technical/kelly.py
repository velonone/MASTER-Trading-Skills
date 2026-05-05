"""
Kelly Criterion Position Sizer
===============================
Implements fractional Kelly sizing for optimal capital allocation
under uncertainty. Uses empirical win rate and payoff ratio.

Reference: Thorp (2006), "The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market"
"""

from decimal import Decimal
from typing import Optional


class KellyPositionSizer:
    """Produces Kelly-optimal position sizes with safety constraints."""

    name = "kelly_position_sizer"
    description = "Fractional Kelly position sizing with drawdown guardrails"
    version = "1.0.0"

    def __init__(
        self,
        fraction: float = 0.25,
        max_position_pct: float = 0.20,
        min_edge: float = 0.01,
    ):
        self.fraction = fraction
        self.max_position_pct = max_position_pct
        self.min_edge = min_edge

    def compute(
        self,
        win_rate: float,
        win_loss_ratio: float,
        current_drawdown: float = 0.0,
    ) -> Optional[Decimal]:
        """
        Args:
            win_rate: Probability of winning [0,1].
            win_loss_ratio: Average win / average loss (reward/risk).
            current_drawdown: Current portfolio drawdown [0,1] for dynamic sizing.

        Returns:
            Optimal position size as fraction of capital, or None if no edge.
        """
        if win_rate <= 0 or win_loss_ratio <= 0:
            return None

        q = 1.0 - win_rate
        full_kelly = (win_loss_ratio * win_rate - q) / win_loss_ratio

        if full_kelly <= self.min_edge:
            return None

        # Fractional Kelly
        size = full_kelly * self.fraction

        # Drawdown compression: reduce size as drawdown deepens
        if current_drawdown > 0.05:
            compression = 1.0 - (current_drawdown / 0.30)  # linear to zero at 30% DD
            size *= max(compression, 0.0)

        # Hard cap
        size = min(size, self.max_position_pct)
        return Decimal(str(max(0.0, size)))

    def batch_compute(
        self,
        opportunities: list[dict],
        portfolio_value: Decimal,
    ) -> list[dict]:
        """Allocate across multiple independent opportunities with correlation guard."""
        results = []
        running_risk = 0.0

        for opp in sorted(opportunities, key=lambda x: x.get("expected_value", 0), reverse=True):
            size_frac = self.compute(
                win_rate=opp["win_rate"],
                win_loss_ratio=opp["win_loss_ratio"],
                current_drawdown=opp.get("current_drawdown", 0.0),
            )
            if size_frac is None:
                continue

            # Correlation penalty: reduce if similar assets already allocated
            corr = opp.get("correlation_to_portfolio", 0.0)
            adjusted = float(size_frac) * (1.0 - corr)
            adjusted = max(0.0, min(adjusted, self.max_position_pct - running_risk))

            if adjusted > 0:
                running_risk += adjusted
                results.append({
                    "symbol": opp["symbol"],
                    "position_size_pct": round(adjusted, 4),
                    "notional": round(float(portfolio_value) * adjusted, 2),
                    "kelly_fraction": float(size_frac),
                })

        return results
