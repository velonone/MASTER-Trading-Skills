"""
Higher-Order Inference Engine
==============================
Implements multi-order thinking, causal-chain reconstruction,
backward induction, and counterfactual reasoning for market events.

All numeric values (chain confidences, singularity weights, signal
thresholds) come from the resolved :class:`Calibration` — never
hard-coded. The default calibration is the bundled VelonLabs Reference
Snapshot, but agents and operators can swap in alternative sources.

All outputs conform to skills.core.types.CausalChain for downstream
consumption by signal and execution layers, plus a `_meta` block
identifying which calibration produced the values.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from skills.core.types import (
    CausalChain,
    CausalEffect,
    EffectOrder,
    EventCategory,
    Signal,
    SignalAction,
)
from skills.inference.calibration import Calibration
from skills.inference.primitives import InferencePrimitive, PrimitiveLibrary


_ORDER_KEYWORD_TO_ENUM = {
    "immediate":   EffectOrder.IMMEDIATE,
    "short_term":  EffectOrder.SHORT_TERM,
    "medium_term": EffectOrder.MEDIUM_TERM,
    "long_term":   EffectOrder.LONG_TERM,
}


class HigherOrderInferenceEngine:
    """
    Core inference engine implementing 2nd/3rd/4th-order effect simulation.

    Construction parameters
    -----------------------
    library
        Optional :class:`PrimitiveLibrary`. If omitted, the library is
        seeded from the active calibration's primitives.

    calibration
        Optional :class:`Calibration`. If omitted, resolves via
        :meth:`Calibration.resolve` (env var → config → bundled snapshot).

    strict_calibration
        If True, raises :class:`CalibrationNotConfigured` when no
        explicit source is configured. Useful for production deployments
        that want to surface a deliberate setup step instead of silently
        falling back to the bundled snapshot.
    """

    def __init__(
        self,
        library: Optional[PrimitiveLibrary] = None,
        *,
        calibration: Optional[Calibration] = None,
        strict_calibration: bool = False,
    ) -> None:
        self.calibration = (
            calibration
            if calibration is not None
            else Calibration.resolve(strict=strict_calibration)
        )
        self.library = (
            library
            if library is not None
            else PrimitiveLibrary.default_library(calibration=self.calibration)
        )
        self.prediction_log: List[Dict[str, Any]] = []
        self.upgrade_log: List[Dict[str, Any]] = []

    # -------------------------------------------------------------------
    # Calibration accessors
    # -------------------------------------------------------------------
    @property
    def _chains(self) -> Dict[str, List[Dict[str, Any]]]:
        return self.calibration.data.get("causal_chains", {})

    @property
    def _singularity(self) -> Dict[str, Any]:
        return self.calibration.data.get("singularity_weights", {})

    @property
    def _signal_thresholds(self) -> Dict[str, float]:
        return self.calibration.data.get("signal_thresholds", {})

    @property
    def _convergence(self) -> Dict[str, float]:
        return self.calibration.data.get("convergence_ratios", {})

    # -------------------------------------------------------------------
    # Layer 1: Singularity Detection
    # -------------------------------------------------------------------

    def detect_singularity(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Determine whether an event has system-altering potential."""
        weights = self._singularity
        score = 0.0
        reasons: List[str] = []

        if event.get("affects_core_assets"):
            score += weights.get("affects_core_assets", 0.0)
            reasons.append("Affects BTC/ETH core assets")

        if event.get("is_public") is False:
            score += weights.get("is_private_information", 0.0)
            reasons.append("Information asymmetry detected")

        if event.get("has_leverage_exposure"):
            score += weights.get("has_leverage_exposure", 0.0)
            reasons.append("Leverage creates positive feedback potential")

        magnitude_weights = weights.get("magnitude", {})
        mag = event.get("magnitude", "small")
        score += magnitude_weights.get(mag, 0.0)

        threshold = weights.get("threshold", 0.5)
        return {
            "is_singularity": score > threshold,
            "score": round(score, 3),
            "threshold": threshold,
            "reasons": reasons,
            "recommendation": "monitor_closely" if score > threshold else "background_noise",
        }

    # -------------------------------------------------------------------
    # Layer 2: Causal Chain Construction
    # -------------------------------------------------------------------

    def build_causal_chain(
        self, event_description: str, category: EventCategory
    ) -> CausalChain:
        """Construct a forward-simulation causal chain from event to equilibrium."""
        effects = self._route_event(event_description, category)
        convergence = self._compute_convergence(effects)
        overall_conf = self._chain_confidence(effects)

        return CausalChain(
            event=event_description,
            category=category,
            timestamp=datetime.utcnow(),
            effects=effects,
            convergence=convergence,
            overall_confidence=overall_conf,
        )

    def _route_event(self, event: str, category: EventCategory) -> List[CausalEffect]:
        event_lower = event.lower()
        if category == EventCategory.WHALE_MOVEMENT:
            return self._whale_chain(event_lower)
        if category == EventCategory.PROTOCOL_CHANGE:
            return self._chain_from_calibration("protocol.generic")
        if category == EventCategory.LISTING:
            return self._chain_from_calibration("listing.generic")
        if category == EventCategory.HACK_EXPLOIT:
            return self._chain_from_calibration("hack.generic")
        if category == EventCategory.LIQUIDATION_CASCADE:
            return self._chain_from_calibration("liquidation.cascade")
        return self._chain_from_calibration("generic.unknown")

    def _whale_chain(self, event: str) -> List[CausalEffect]:
        if "deposit" in event and "exchange" in event:
            return self._chain_from_calibration("whale.exchange_deposit")
        if "accumulation" in event or "accumulating" in event:
            return self._chain_from_calibration("whale.accumulation")
        return self._chain_from_calibration("generic.unknown")

    def _chain_from_calibration(self, key: str) -> List[CausalEffect]:
        """Materialize a causal chain from the calibration JSON."""
        chain_data = self._chains.get(key) or self._chains.get("generic.unknown", [])
        effects: List[CausalEffect] = []
        for step in chain_data:
            order_enum = _ORDER_KEYWORD_TO_ENUM.get(step.get("order", "immediate"),
                                                    EffectOrder.IMMEDIATE)
            effects.append(CausalEffect(
                description=step.get("description", ""),
                order=order_enum,
                confidence=float(step.get("confidence", 0.5)),
                affected_assets=list(step.get("affected_assets", [])),
                direction=step.get("direction", "neutral"),
                magnitude=step.get("magnitude", "small"),
            ))
        return effects

    def _compute_convergence(self, effects: List[CausalEffect]) -> str:
        if not effects:
            return "insufficient_data"
        bullish = sum(e.confidence for e in effects if e.direction == "bullish")
        bearish = sum(e.confidence for e in effects if e.direction == "bearish")
        bull_factor = self._convergence.get("bullish_factor", 1.5)
        bear_factor = self._convergence.get("bearish_factor", 1.5)
        if bullish > bearish * bull_factor:
            return "bullish_convergence"
        if bearish > bullish * bear_factor:
            return "bearish_convergence"
        return "range_bound_uncertain"

    def _chain_confidence(self, effects: List[CausalEffect]) -> float:
        if not effects:
            return 0.0
        product = 1.0
        for e in effects:
            product *= e.confidence
        decay = self._signal_thresholds.get("chain_length_decay", 0.95)
        length_penalty = decay ** len(effects)
        return round(product * length_penalty, 4)

    # -------------------------------------------------------------------
    # Layer 3: Backward Induction & Counterfactuals
    # -------------------------------------------------------------------

    def backward_induction(
        self, desired_outcome: str, constraints: List[str]
    ) -> List[str]:
        """Game-theoretic backward induction from a desired outcome."""
        steps: List[str] = []
        outcome_lower = desired_outcome.lower()

        if "profit" in outcome_lower:
            steps.extend([
                "Exit position at target price or trailing stop",
                "Set take-profit and stop-loss orders",
                "Monitor for adverse divergence signals",
                "Enter position at optimal limit price",
                "Confirm entry signal with multi-timeframe confluence",
                "Analyze market regime and liquidity conditions",
            ])
        elif "hedge" in outcome_lower:
            steps.extend([
                "Unwind hedge as risk dissipates",
                "Rebalance hedge ratio dynamically",
                "Enter correlated inverse position",
                "Identify exposure concentration risk",
            ])
        else:
            steps.append("Decompose desired outcome into atomic actions")

        return list(reversed(steps))

    def counterfactual_analysis(self, event: str, observed_effect: str) -> Dict[str, Any]:
        """Assess whether the event actually caused the observed effect."""
        alternatives = [
            "Market-wide macro movement (not event-specific)",
            "Pre-existing trend continuation",
            "Coincidental timing with unrelated catalyst",
            "Correlated confounding variable",
        ]
        return {
            "event": event,
            "observed_effect": observed_effect,
            "alternative_explanations": alternatives,
            "verification_checklist": [
                "Check if similar assets moved in parallel",
                "Determine whether trend existed pre-event",
                "Search historical precedent for same event type",
                "Quantify information surprise (entropy drop)",
            ],
        }

    # -------------------------------------------------------------------
    # Layer 4: Signal Generation
    # -------------------------------------------------------------------

    def generate_prediction(
        self, event_description: str, category: EventCategory
    ) -> Dict[str, Any]:
        """End-to-end prediction pipeline; output includes calibration provenance."""
        singularity = self.detect_singularity({"affects_core_assets": True, "magnitude": "medium"})
        chain = self.build_causal_chain(event_description, category)
        signal_action = self._chain_to_signal(chain)

        prediction = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_description,
            "category": category.value,
            "is_singularity": singularity["is_singularity"],
            "singularity_score": singularity["score"],
            "causal_chain": [e.model_dump() for e in chain.effects],
            "convergence": chain.convergence,
            "overall_confidence": chain.overall_confidence,
            "signal_action": signal_action.value,
            "primitive_references": self._match_primitives(event_description),
            "_meta": self.calibration.emit_meta(),
        }
        self.prediction_log.append(prediction)
        return prediction

    def _chain_to_signal(self, chain: CausalChain) -> SignalAction:
        thresholds = self._signal_thresholds
        hold_below = thresholds.get("hold_below", 0.30)
        buy_above = thresholds.get("buy_above", 0.60)
        sell_above = thresholds.get("sell_above", 0.60)

        if chain.overall_confidence < hold_below:
            return SignalAction.HOLD
        if "bullish" in chain.convergence:
            return SignalAction.BUY if chain.overall_confidence > buy_above else SignalAction.HOLD
        if "bearish" in chain.convergence:
            return SignalAction.SELL if chain.overall_confidence > sell_above else SignalAction.REDUCE
        return SignalAction.HOLD

    def _match_primitives(self, event: str) -> List[str]:
        """Map event text to relevant primitives for traceability."""
        matched: List[str] = []
        event_lower = event.lower()
        for name, primitive in self.library.primitives.items():
            if any(token in event_lower for token in primitive.tags):
                matched.append(name)
        return matched

    # -------------------------------------------------------------------
    # Self-Upgrade Diagnostics
    # -------------------------------------------------------------------

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "total_predictions": len(self.prediction_log),
            "primitives_count": len(self.library.primitives),
            "primitive_accuracy": self.library.accuracy_report(),
            "underperformers": [
                p.name for p in self.library.underperformers()
            ],
            "upgrade_recommendations": self._generate_recommendations(),
            "calibration": self.calibration.emit_meta(),
        }

    def _generate_recommendations(self) -> List[str]:
        recs: List[str] = []
        for p in self.library.underperformers():
            recs.append(
                f"REVIEW primitive '{p.name}': accuracy {p.accuracy:.2f} "
                f"after {p.times_used} uses. Consider recalibration or retirement."
            )
        unused = [n for n, p in self.library.primitives.items() if p.times_used == 0]
        if unused:
            recs.append(f"UNUSED primitives: {unused}. Validate relevance or remove.")
        warning = self.calibration.freshness_warning()
        if warning:
            recs.append(f"CALIBRATION: {warning}")
        return recs

    def export_log(self, path: Optional[str] = None) -> str:
        """Serialize prediction log for offline analysis."""
        payload = {
            "engine": "HigherOrderInferenceEngine",
            "exported_at": datetime.utcnow().isoformat(),
            "calibration": self.calibration.emit_meta(),
            "predictions": self.prediction_log,
            "diagnostics": self.diagnostics(),
        }
        json_str = json.dumps(payload, indent=2, default=str)
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(json_str)
        return json_str
