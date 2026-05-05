"""
Broker Simulation & Slippage Models
=====================================
Realistic fill simulation for backtesting.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class FillResult:
    price: float
    quantity: float
    slippage_bps: float
    fee: float
    timestamp: str | None = None


class SlippageModel:
    def apply(self, order_qty: float, bar: dict, side: str) -> float:
        raise NotImplementedError


class VolatilitySlippage(SlippageModel):
    """
    Slippage = base_bps + volatility_factor * sqrt(order_size / avg_volume)
    Reference: Almgren & Chriss (2000) market impact model (simplified)
    """

    def __init__(self, base_bps: float = 2.0, volatility_factor: float = 5.0):
        self.base_bps = base_bps
        self.volatility_factor = volatility_factor

    def apply(self, order_qty: float, bar: dict, side: str) -> float:
        avg_volume = bar.get("volume", 1.0)
        if avg_volume <= 0:
            avg_volume = 1.0
        vol = (
            bar.get("atr_14", bar["high"] - bar["low"]) / bar["close"] if bar["close"] > 0 else 0.01
        )
        size_ratio = abs(order_qty) / avg_volume
        slippage = self.base_bps + self.volatility_factor * vol * 100 * np.sqrt(size_ratio)
        return slippage


class BrokerSimulator:
    """Simulates order fills against historical bar data."""

    def __init__(
        self,
        slippage_model: SlippageModel | None = None,
        commission_rate: float = 0.0004,
        allow_short: bool = True,
    ):
        self.slippage = slippage_model or VolatilitySlippage()
        self.commission_rate = commission_rate
        self.allow_short = allow_short

    def simulate_market_order(self, qty: float, bar: dict, side: str) -> FillResult:
        """
        Args:
            qty: Order quantity (positive).
            bar: Dict with open, high, low, close, volume.
            side: 'buy' or 'sell'.
        """
        # Use open price of next bar for fill (realistic lookahead-free)
        fill_price = bar["open"]
        slippage_bps = self.slippage.apply(qty, bar, side)

        # Adjust fill price against trader
        slippage_pct = slippage_bps / 10000.0
        if side == "buy":
            fill_price *= 1 + slippage_pct
        else:
            fill_price *= 1 - slippage_pct

        fill_price = max(bar["low"], min(bar["high"], fill_price))
        notional = fill_price * qty
        fee = notional * self.commission_rate

        return FillResult(
            price=round(fill_price, 8),
            quantity=qty,
            slippage_bps=round(slippage_bps, 2),
            fee=round(fee, 8),
        )

    def simulate_limit_order(
        self, qty: float, limit_price: float, bar: dict, side: str
    ) -> FillResult | None:
        """
        Limit order fills if price crosses limit within bar.
        Two-step logic removes lookahead bias:
          1. Check if open already crossed the limit (known at bar start).
          2. If not, check if the bar's range later touched the limit.
        """
        if side == "buy":
            if bar["open"] <= limit_price:
                # Open already at or below limit — fill at open
                fill_price = bar["open"]
            elif bar["low"] <= limit_price:
                # Price touched limit later in bar — conservative fill at limit
                fill_price = limit_price
            else:
                return None
        elif side == "sell":
            if bar["open"] >= limit_price:
                fill_price = bar["open"]
            elif bar["high"] >= limit_price:
                fill_price = limit_price
            else:
                return None
        else:
            return None

        notional = fill_price * qty
        fee = notional * self.commission_rate
        return FillResult(
            price=round(fill_price, 8),
            quantity=qty,
            slippage_bps=0.0,
            fee=round(fee, 8),
        )
