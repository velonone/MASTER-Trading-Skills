"""
Adversarial RL Market Maker — Robust Execution Policy
======================================================
Trains a market-maker policy against an adversarial environment
that simulates worst-case market conditions (adverse selection,
inventory risk, latency arbitrage).

Reference: Spooner & Mayberry (2020), arXiv:2003.01820
"""

from typing import Dict, List, Tuple

import numpy as np


class AdversarialMarketMaker:
    """
    Zero-sum adversarial framework for market-making strategy robustness.
    This is a lightweight, rule-based skeleton; full training requires
    Stable-Baselines3 + custom Gymnasium environment.
    """

    name = "adversarial_market_maker"
    description = "Adversarially robust market-making policy skeleton"
    version = "1.0.0"

    def __init__(self, spread_bps: float = 5.0, inventory_limit: float = 1.0):
        self.spread_bps = spread_bps
        self.inventory_limit = inventory_limit
        self.inventory = 0.0
        self.pnl = 0.0

    def quote(
        self, mid_price: float, volatility: float, inventory: float
    ) -> Tuple[float, float]:
        """
        Args:
            mid_price: Current mid-price.
            volatility: Annualized volatility estimate (e.g. 0.60 for 60%).
            inventory: Current inventory in units of notional.

        Returns:
            (bid_price, ask_price)
        """
        # Adversarial spread: widen with volatility
        half_spread = mid_price * (self.spread_bps / 10000.0) * (1.0 + volatility)

        # Inventory skew: skew quotes to reduce imbalance
        skew = np.tanh(inventory / self.inventory_limit) * half_spread * 0.5

        bid = mid_price - half_spread - skew
        ask = mid_price + half_spread - skew
        return round(bid, 8), round(ask, 8)

    def on_fill(self, side: str, price: float, qty: float, mid: float) -> Dict[str, float]:
        """Update inventory and realized PnL on fill."""
        if side == "buy":
            self.inventory += qty
            self.pnl -= (price - mid) * qty
        else:
            self.inventory -= qty
            self.pnl += (mid - price) * qty

        return {
            "inventory": round(self.inventory, 6),
            "realized_pnl": round(self.pnl, 4),
            "unrealized_pnl": round(self.inventory * (mid - price), 4),
        }

    def adversarial_stress_test(
        self, paths: List[np.ndarray], adversary_intensity: float = 0.3
    ) -> Dict[str, float]:
        """
        Simulate worst-case adverse selection.

        Args:
            paths: List of price path arrays.
            adversary_intensity: Probability of informed flow (0–1).

        Returns:
            Summary statistics under stress.
        """
        pnls = []
        max_inv = []
        for path in paths:
            self.inventory = 0.0
            self.pnl = 0.0
            for t in range(1, len(path)):
                mid = path[t]
                vol = np.std(path[max(0, t - 20) : t + 1]) / mid if mid > 0 else 0.0
                bid, ask = self.quote(mid, vol, self.inventory)

                # Adversary sends informed orders against us
                if np.random.rand() < adversary_intensity:
                    if path[t] > path[t - 1]:  # Adversary knows up-move
                        self.on_fill("sell", bid, 0.1, mid)
                    else:
                        self.on_fill("buy", ask, 0.1, mid)
                else:
                    # Uninformed noise flow
                    if np.random.rand() < 0.5:
                        self.on_fill("buy", bid, 0.05, mid)
                    else:
                        self.on_fill("sell", ask, 0.05, mid)

            pnls.append(self.pnl)
            max_inv.append(abs(self.inventory))

        return {
            "mean_pnl": round(float(np.mean(pnls)), 4),
            "std_pnl": round(float(np.std(pnls)), 4),
            "worst_pnl": round(float(np.min(pnls)), 4),
            "avg_max_inventory": round(float(np.mean(max_inv)), 4),
            "sharpe": round(float(np.mean(pnls) / (np.std(pnls) + 1e-10)), 4),
        }
