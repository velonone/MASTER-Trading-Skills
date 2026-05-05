"""
FOMO / Panic / Greed Detection Engine
======================================
Quantifies behavioral extremes in market data using momentum,
volume anomalies, and acceleration profiles.

Emits standardized Signal objects for downstream risk and execution.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np

from skills.core.base import BaseSkill
from skills.core.types import Signal, SignalAction


class FOMODetector(BaseSkill):
    """
    Detects Fear-Of-Missing-Out (FOMO) and panic regimes from price
    and volume dynamics. Calibrated for crypto's high-volatility regime.
    """

    name = "fomo_detector"
    description = "Behavioral-extreme detection for sentiment-aware trading"
    version = "2.0.0"
    triggers = ["fomo", "panic", "greed", "sentiment", "behavioral"]

    def __init__(self):
        self.thresholds = {
            "price_momentum": 0.15,
            "volume_surge": 2.0,
            "price_acceleration": 0.05,
            "new_high_proximity": 0.98,
        }
        self.weights = {
            "momentum": 0.30,
            "volume": 0.30,
            "acceleration": 0.20,
            "new_high": 0.20,
        }

    def detect(
        self,
        symbol: str,
        prices: list[float],
        volumes: list[float],
        market_cap: float | None = None,
    ) -> Signal:
        """
        Args:
            prices: Chronological price series (oldest first).
            volumes: Chronological volume series.
            market_cap: Optional market cap for volume normalization.

        Returns:
            Standardized Signal with FOMO score and recommendation.
        """
        if len(prices) < 3 or len(volumes) < 1:
            return self._no_data_signal(symbol)

        metrics = {}
        evidence: list[str] = []
        score = 0.0

        # 1. Price momentum
        m_score, m_ev = self._momentum(prices)
        score += m_score * self.weights["momentum"]
        metrics["momentum"] = round(m_score, 4)
        if m_ev:
            evidence.append(m_ev)

        # 2. Volume surge
        v_score, v_ev = self._volume_surge(volumes, market_cap)
        score += v_score * self.weights["volume"]
        metrics["volume_surge"] = round(v_score, 4)
        if v_ev:
            evidence.append(v_ev)

        # 3. Price acceleration
        a_score, a_ev = self._acceleration(prices)
        score += a_score * self.weights["acceleration"]
        metrics["acceleration"] = round(a_score, 4)
        if a_ev:
            evidence.append(a_ev)

        # 4. New high proximity
        h_score, h_ev = self._new_high(prices)
        score += h_score * self.weights["new_high"]
        metrics["new_high"] = round(h_score, 4)
        if h_ev:
            evidence.append(h_ev)

        fomo_score = score * 100.0
        confidence = min(0.5 + len(evidence) * 0.12, 0.95)

        if fomo_score > 80:
            action = SignalAction.SELL
            rec = "STRONG_SELL: Extreme FOMO regime; distribution likely"
        elif fomo_score > 60:
            action = SignalAction.REDUCE
            rec = "REDUCE: Elevated FOMO; consider profit-taking"
        elif fomo_score < 20 and m_score < 0:
            action = SignalAction.BUY
            rec = "BUY: Panic regime detected; potential accumulation zone"
        else:
            action = SignalAction.HOLD
            rec = "HOLD: No behavioral extreme detected"

        return Signal(
            action=action,
            confidence=round(confidence, 3),
            strength=round(score, 3),
            symbol=symbol,
            source=self.name,
            metadata={"fomo_score": round(fomo_score, 2), **metrics},
            evidence=evidence + [rec],
            timestamp=datetime.utcnow(),
        )

    def _momentum(self, prices: list[float]) -> tuple[float, str]:
        if len(prices) < 2:
            return 0.0, ""
        mom = (prices[-1] - prices[0]) / prices[0]
        score = min(max(mom / self.thresholds["price_momentum"], 0.0), 1.0)
        ev = f"Price momentum {mom:+.1%}" if abs(mom) > 0.05 else ""
        return score, ev

    def _volume_surge(self, volumes: list[float], market_cap: float | None) -> tuple[float, str]:
        if len(volumes) < 2:
            return 0.0, ""
        current = volumes[-1]
        baseline = np.mean(volumes[:-1]) if len(volumes) > 1 else current
        if baseline == 0:
            return 0.0, ""
        ratio = current / baseline
        score = min(ratio / self.thresholds["volume_surge"], 1.0)
        ev = f"Volume surge {ratio:.1f}x baseline" if ratio > 1.5 else ""
        return score, ev

    def _acceleration(self, prices: list[float]) -> tuple[float, str]:
        if len(prices) < 3:
            return 0.0, ""
        r1 = (prices[-2] - prices[0]) / prices[0]
        r2 = (prices[-1] - prices[-2]) / prices[-2]
        accel = r2 - r1
        score = min(max(accel / self.thresholds["price_acceleration"], 0.0), 1.0)
        ev = f"Price acceleration {accel:+.1%}" if abs(accel) > 0.03 else ""
        return score, ev

    def _new_high(self, prices: list[float]) -> tuple[float, str]:
        if len(prices) < 2:
            return 0.0, ""
        prev_max = max(prices[:-1])
        curr = prices[-1]
        if curr > prev_max:
            breakthrough = (curr - prev_max) / prev_max
            score = min(breakthrough / 0.05, 1.0)
            return score, f"New high breakthrough {breakthrough:+.1%}"
        proximity = curr / prev_max
        if proximity > self.thresholds["new_high_proximity"]:
            score = (proximity - self.thresholds["new_high_proximity"]) / (
                1.0 - self.thresholds["new_high_proximity"]
            )
            return score, f"Near high proximity {proximity:.1%}"
        return 0.0, ""

    async def run(self, context: dict) -> Signal:
        """Agent dispatch entrypoint."""
        return self.detect(
            symbol=context.get("symbol", "BTC/USDT"),
            prices=context.get("prices", []),
            volumes=context.get("volumes", []),
            market_cap=context.get("market_cap"),
        )

    def _no_data_signal(self, symbol: str) -> Signal:
        return Signal(
            action=SignalAction.HOLD,
            confidence=0.0,
            strength=0.0,
            symbol=symbol,
            source=self.name,
            evidence=["Insufficient data for behavioral analysis"],
        )
