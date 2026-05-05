"""
Largest Lyapunov Exponent (LLE) — Chaos Detection
==================================================
Quantifies the rate of divergence of initially close trajectories
in reconstructed phase space. Positive LLE → chaotic (short-term
predictable) dynamics.

Reference: Rosenstein et al. (1993), "A practical method for calculating LLE"
"""

import numpy as np


class LyapunovExponentAnalyzer:
    """Computes LLE from a scalar time series using time-delay embedding."""

    name = "lyapunov_exponent_analyzer"
    description = "Detects chaotic market regimes via largest Lyapunov exponent"
    version = "1.0.0"

    def __init__(self, embedding_dim: int = 4, lag: int = 1, min_sep: int = 10):
        self.embedding_dim = embedding_dim
        self.lag = lag
        self.min_sep = min_sep

    def compute(self, series: np.ndarray) -> dict:
        """
        Args:
            series: 1-D numpy array of prices or returns.

        Returns:
            Dict with largest_lyapunov_exponent, regime classification, and metadata.
        """
        n = len(series)
        m = n - (self.embedding_dim - 1) * self.lag
        if m <= self.min_sep * 2:
            return {"lle": 0.0, "regime": "insufficient_data", "error": "Series too short"}

        # Time-delay embedding
        embedded = np.array(
            [[series[i + j * self.lag] for j in range(self.embedding_dim)] for i in range(m)]
        )

        divergences = []
        for i in range(m - self.min_sep):
            distances = np.linalg.norm(embedded - embedded[i], axis=1)
            # Exclude temporally close neighbors
            distances[max(0, i - self.min_sep) : min(m, i + self.min_sep)] = np.inf
            j = np.argmin(distances)

            div = []
            max_k = min(50, m - max(i, j))
            for k in range(max_k):
                d = np.linalg.norm(embedded[i + k] - embedded[j + k])
                if d > 0:
                    div.append(np.log(d))
            if len(div) > 10:
                divergences.append(div)

        if not divergences:
            return {"lle": 0.0, "regime": "uncertain", "error": "No valid divergence pairs"}

        # Average divergence curve
        max_len = max(len(d) for d in divergences)
        avg_div = np.zeros(max_len)
        counts = np.zeros(max_len)
        for div in divergences:
            for idx, val in enumerate(div):
                avg_div[idx] += val
                counts[idx] += 1
        valid = counts > 0
        avg_div[valid] /= counts[valid]

        # Linear fit on early divergence (avoid noise floor)
        fit_points = min(20, max_len)
        slope, _ = np.polyfit(range(fit_points), avg_div[:fit_points], 1)

        regime = (
            "chaotic" if slope > 0.01 else
            "stable" if slope < -0.01 else
            "neutral"
        )

        return {
            "lle": round(float(slope), 6),
            "regime": regime,
            "embedding_dim": self.embedding_dim,
            "lag": self.lag,
            "interpretation": (
                "Short-term predictability possible" if regime == "chaotic" else
                "Mean-reverting or stable dynamics" if regime == "stable" else
                "No clear dynamical signature"
            ),
        }
