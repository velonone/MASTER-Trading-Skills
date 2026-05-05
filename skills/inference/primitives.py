"""
Inference Primitives — Reusable Causal Patterns
=================================================
Each primitive encodes a empirically-observed market regularity
with Bayesian tracking of its predictive accuracy.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class InferencePrimitive(BaseModel):
    """
    A reusable inference pattern with self-updating accuracy tracking.
    """
    name: str
    category: str = Field(default="general", description="e.g. game_theory, system_dynamics, causal")
    condition: str = Field(..., description="Observable trigger condition")
    conclusion: str = Field(..., description="Predicted market outcome")
    base_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    times_used: int = 0
    times_correct: int = 0
    last_used: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)

    @property
    def accuracy(self) -> float:
        if self.times_used == 0:
            return 0.5
        return self.times_correct / self.times_used

    @property
    def calibrated_confidence(self) -> float:
        """Down-weight base confidence by empirical track record."""
        # Bayesian shrinkage toward empirical accuracy
        return self.base_confidence * (0.3 + 0.7 * self.accuracy)

    def record_outcome(self, was_correct: bool) -> None:
        self.times_used += 1
        if was_correct:
            self.times_correct += 1
        self.last_used = datetime.utcnow()


class PrimitiveLibrary(BaseModel):
    """In-memory collection of inference primitives with query utilities."""

    primitives: Dict[str, InferencePrimitive] = Field(default_factory=dict)

    def add(self, primitive: InferencePrimitive, override: bool = False) -> None:
        if primitive.name in self.primitives and not override:
            raise KeyError(f"Primitive '{primitive.name}' already exists.")
        self.primitives[primitive.name] = primitive

    def get(self, name: str) -> Optional[InferencePrimitive]:
        return self.primitives.get(name)

    def find_by_tag(self, tag: str) -> List[InferencePrimitive]:
        return [p for p in self.primitives.values() if tag in p.tags]

    def find_by_category(self, category: str) -> List[InferencePrimitive]:
        return [p for p in self.primitives.values() if p.category == category]

    def underperformers(self, min_uses: int = 5, threshold: float = 0.4) -> List[InferencePrimitive]:
        """Return primitives whose empirical accuracy is below threshold."""
        return [
            p for p in self.primitives.values()
            if p.times_used >= min_uses and p.accuracy < threshold
        ]

    def accuracy_report(self) -> Dict[str, float]:
        return {name: p.accuracy for name, p in self.primitives.items() if p.times_used > 0}

    @classmethod
    def default_library(cls, calibration: Optional["object"] = None) -> "PrimitiveLibrary":
        """
        Bootstrap with core market primitives.

        By default, primitives are loaded from the resolved calibration
        (see :class:`skills.inference.calibration.Calibration`). The
        bundled VelonLabs Reference Snapshot provides real-world values;
        users can override by configuring a different calibration source.
        """
        # Local import to avoid a circular dependency at module load time.
        from skills.inference.calibration import Calibration

        cal = calibration if calibration is not None else Calibration.resolve()
        lib = cls()
        for name, spec in cal.data.get("primitives", {}).items():
            lib.add(InferencePrimitive(
                name=name,
                category=spec.get("category", "general"),
                condition=spec["condition"],
                conclusion=spec["conclusion"],
                base_confidence=spec.get("base_confidence", 0.5),
                tags=list(spec.get("tags", [])),
            ))
        return lib
