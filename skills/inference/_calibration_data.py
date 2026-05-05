"""
VelonLabs Reference Calibration · Snapshot v2026.05
====================================================
Single source of truth for calibration constants used by the inference
layer. Released as a free MIT-licensed reference baseline.

Origin: derived from VelonLabs internal calibration process against
crypto market data 2020-01 to 2026-04.

Markets evolve. These values reflect observed behavior up to the
released_at date below; their predictive power decays over time.
Updated snapshots ship as PRs to this file (community-maintained).

Usage modes (see skills.inference.calibration.Calibration):

  snapshot   — load this file directly (default, what you see here)
  self       — run tools/calibrate.py against your own trade history
  custom     — load any user-provided JSON with the same shape

When redistributing or building products on top of these values, please
keep the "VelonLabs Reference Calibration" attribution intact in any
downstream documentation, audit logs, or research output.
"""

from __future__ import annotations

from typing import Any

VELONLABS_SNAPSHOT_2026_05: dict[str, Any] = {
    # ------------------------------------------------------------------
    # Provenance
    # ------------------------------------------------------------------
    "version": "2026.05",
    "released_at": "2026-05-01",
    "source": "velonlabs_snapshot",
    "calibrated_against": {
        "start": "2020-01-01",
        "end": "2026-04-30",
        "markets": ["crypto_spot", "crypto_perp"],
    },
    "attribution": "VelonLabs Reference Calibration",
    "license_note": (
        "Calibration values released under MIT alongside code. "
        "Attribution requested in published research and commercial use."
    ),
    # ------------------------------------------------------------------
    # Inference primitives — base_confidence is the prior before any
    # empirical track record adjusts it (see InferencePrimitive.calibrated_confidence)
    # ------------------------------------------------------------------
    "primitives": {
        "whale_exchange_deposit": {
            "category": "game_theory",
            "condition": "Whale deposits >$1M to centralized exchange",
            "conclusion": "Sell pressure incoming within 72h",
            "base_confidence": 0.75,
            "tags": ["whale", "exchange", "supply_shock"],
        },
        "whale_accumulation_pattern": {
            "category": "system_dynamics",
            "condition": "Whale splits purchases across 5+ wallets over 7+ days",
            "conclusion": "Strategic accumulation, bullish medium-term",
            "base_confidence": 0.70,
            "tags": ["whale", "accumulation", "supply_squeeze"],
        },
        "tvl_price_divergence": {
            "category": "system_dynamics",
            "condition": "TVL decreasing while token price increasing",
            "conclusion": "Unsustainable pump, correction likely",
            "base_confidence": 0.80,
            "tags": ["defi", "tvl", "divergence", "warning"],
        },
        "yield_compression": {
            "category": "causal",
            "condition": "DeFi yields falling below risk-free rate",
            "conclusion": "Capital outflow imminent",
            "base_confidence": 0.85,
            "tags": ["defi", "yield", "macro"],
        },
        "liquidation_cascade_setup": {
            "category": "feedback_loop",
            "condition": "Open Interest > 30% of market cap AND bid depth < 50% normal",
            "conclusion": "Flash crash risk elevated",
            "base_confidence": 0.70,
            "tags": ["derivatives", "liquidation", "volatility"],
        },
        "governance_whale_alignment": {
            "category": "game_theory",
            "condition": "Top 5 wallets voting same direction on governance proposal",
            "conclusion": "Proposal will pass with >80% probability",
            "base_confidence": 0.85,
            "tags": ["governance", "dao", "voting"],
        },
        "funding_extreme_mean_reversion": {
            "category": "statistical",
            "condition": "Perpetual funding rate > |0.1%| sustained 3+ intervals",
            "conclusion": "Mean reversion expected; counter-trade profitable",
            "base_confidence": 0.72,
            "tags": ["perpetual", "funding", "mean_reversion"],
        },
        "oi_spike_without_price": {
            "category": "manipulation",
            "condition": "Open interest spikes >20% without corresponding price move",
            "conclusion": "Potential spoofing or wash trading",
            "base_confidence": 0.65,
            "tags": ["derivatives", "manipulation", "alert"],
        },
    },
    # ------------------------------------------------------------------
    # Causal chains — keyed by "<category>.<sub_pattern>"
    # Each step lists order, confidence, magnitude, direction, asset_scope
    # ------------------------------------------------------------------
    "causal_chains": {
        "whale.exchange_deposit": [
            {
                "order": "immediate",
                "confidence": 0.85,
                "direction": "bearish",
                "magnitude": "medium",
                "description": "Sell order placement likely within hours",
                "affected_assets": ["underlying_token"],
            },
            {
                "order": "short_term",
                "confidence": 0.75,
                "direction": "bearish",
                "magnitude": "medium",
                "description": "Price pressure as order absorbs bid depth",
                "affected_assets": ["underlying_token"],
            },
            {
                "order": "medium_term",
                "confidence": 0.50,
                "direction": "bearish",
                "magnitude": "large",
                "description": "Herding behavior: other whales may follow",
                "affected_assets": ["underlying_token", "sector_index"],
            },
            {
                "order": "long_term",
                "confidence": 0.60,
                "direction": "neutral",
                "magnitude": "small",
                "description": "New equilibrium at lower clearing price",
                "affected_assets": ["underlying_token"],
            },
        ],
        "whale.accumulation": [
            {
                "order": "immediate",
                "confidence": 0.80,
                "direction": "bullish",
                "magnitude": "small",
                "description": "Buying pressure incrementally absorbs ask depth",
                "affected_assets": ["underlying_token"],
            },
            {
                "order": "short_term",
                "confidence": 0.85,
                "direction": "bullish",
                "magnitude": "medium",
                "description": "Exchange supply decreases; supply squeeze forms",
                "affected_assets": ["underlying_token"],
            },
            {
                "order": "medium_term",
                "confidence": 0.65,
                "direction": "bullish",
                "magnitude": "large",
                "description": "Price discovery shifts to higher equilibrium",
                "affected_assets": ["underlying_token"],
            },
        ],
        "protocol.generic": [
            {
                "order": "immediate",
                "confidence": 0.90,
                "direction": "neutral",
                "magnitude": "small",
                "description": "Market participants evaluate impact on positions",
                "affected_assets": ["protocol_token"],
            },
            {
                "order": "short_term",
                "confidence": 0.75,
                "direction": "neutral",
                "magnitude": "medium",
                "description": "Capital reallocation across competing protocols begins",
                "affected_assets": ["protocol_token", "competitors"],
            },
            {
                "order": "medium_term",
                "confidence": 0.70,
                "direction": "neutral",
                "magnitude": "medium",
                "description": "New yield/utility equilibrium established",
                "affected_assets": ["defi_sector"],
            },
        ],
        "listing.generic": [
            {
                "order": "immediate",
                "confidence": 0.95,
                "direction": "bullish",
                "magnitude": "large",
                "description": "Price spike from news-driven demand shock",
                "affected_assets": ["listed_token"],
            },
            {
                "order": "short_term",
                "confidence": 0.90,
                "direction": "neutral",
                "magnitude": "medium",
                "description": "Arbitrage between DEX and CEX tightens spread",
                "affected_assets": ["listed_token"],
            },
            {
                "order": "medium_term",
                "confidence": 0.80,
                "direction": "bearish",
                "magnitude": "medium",
                "description": "Early holders distribute to new retail entrants",
                "affected_assets": ["listed_token"],
            },
            {
                "order": "long_term",
                "confidence": 0.60,
                "direction": "neutral",
                "magnitude": "small",
                "description": "New price floor established post-distribution",
                "affected_assets": ["listed_token"],
            },
        ],
        "hack.generic": [
            {
                "order": "immediate",
                "confidence": 0.95,
                "direction": "bearish",
                "magnitude": "extreme",
                "description": "Attacker dumps stolen tokens immediately",
                "affected_assets": ["hacked_token"],
            },
            {
                "order": "short_term",
                "confidence": 0.85,
                "direction": "bearish",
                "magnitude": "large",
                "description": "Contagion fear spreads to similar protocols",
                "affected_assets": ["similar_protocols"],
            },
            {
                "order": "medium_term",
                "confidence": 0.70,
                "direction": "bearish",
                "magnitude": "large",
                "description": "TVL exodus from entire vertical",
                "affected_assets": ["sector"],
            },
            {
                "order": "long_term",
                "confidence": 0.75,
                "direction": "bullish",
                "magnitude": "medium",
                "description": "Survivors capture market share",
                "affected_assets": ["surviving_protocols"],
            },
        ],
        "liquidation.cascade": [
            {
                "order": "immediate",
                "confidence": 0.95,
                "direction": "bearish",
                "magnitude": "extreme",
                "description": "Liquidation bots trigger stop-market orders",
                "affected_assets": ["liquidated_asset"],
            },
            {
                "order": "short_term",
                "confidence": 0.88,
                "direction": "bearish",
                "magnitude": "extreme",
                "description": "Cascading deleveraging as underwater positions close",
                "affected_assets": ["liquidated_asset", "correlated_assets"],
            },
            {
                "order": "medium_term",
                "confidence": 0.70,
                "direction": "neutral",
                "magnitude": "medium",
                "description": "Funding rates turn highly negative; shorts pay longs",
                "affected_assets": ["perpetual_markets"],
            },
            {
                "order": "long_term",
                "confidence": 0.55,
                "direction": "bullish",
                "magnitude": "large",
                "description": "Capitulation bottom; mean reversion setup",
                "affected_assets": ["liquidated_asset"],
            },
        ],
        "generic.unknown": [
            {
                "order": "immediate",
                "confidence": 0.50,
                "direction": "neutral",
                "magnitude": "small",
                "description": "Initial market reaction undetermined",
                "affected_assets": ["general"],
            },
        ],
    },
    # ------------------------------------------------------------------
    # Singularity scoring — what makes an event "system-altering"
    # ------------------------------------------------------------------
    "singularity_weights": {
        "affects_core_assets": 0.30,
        "is_private_information": 0.20,
        "has_leverage_exposure": 0.25,
        "magnitude": {
            "small": 0.0,
            "medium": 0.10,
            "large": 0.20,
            "extreme": 0.30,
        },
        "threshold": 0.50,
    },
    # ------------------------------------------------------------------
    # Signal generation thresholds — bridge from confidence to action
    # ------------------------------------------------------------------
    "signal_thresholds": {
        "hold_below": 0.30,  # < this → HOLD
        "buy_above": 0.60,  # ≥ this → BUY (if bullish)
        "sell_above": 0.60,  # ≥ this → SELL (if bearish)
        "confidence_floor": 0.55,  # risk manager suppresses signals below this
        "chain_length_decay": 0.95,  # multiplicative penalty per causal step
    },
    # ------------------------------------------------------------------
    # Convergence detection — when does a chain "agree" on direction?
    # ------------------------------------------------------------------
    "convergence_ratios": {
        "bullish_factor": 1.5,  # bullish_sum > bearish_sum * 1.5
        "bearish_factor": 1.5,
    },
}


# Default snapshot exported for convenience.
DEFAULT_SNAPSHOT = VELONLABS_SNAPSHOT_2026_05
