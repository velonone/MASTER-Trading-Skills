"""
Inference Layer — Higher-Order Reasoning Engine
================================================
Provides multi-order causal reasoning, singularity detection,
and self-upgrading primitives for predictive market analysis.

Entry Points:
    from skills.inference import HigherOrderInferenceEngine
    engine = HigherOrderInferenceEngine()
    prediction = engine.generate_prediction(event, category)
"""

from skills.inference.calibration import (
    Calibration,
    CalibrationNotConfigured,
    CalibrationSource,
    SETUP_PROMPT,
)
from skills.inference.engine import HigherOrderInferenceEngine
from skills.inference.primitives import InferencePrimitive, PrimitiveLibrary
from skills.inference.setup_skill import CalibrationSetupSkill

__all__ = [
    "Calibration",
    "CalibrationNotConfigured",
    "CalibrationSetupSkill",
    "CalibrationSource",
    "HigherOrderInferenceEngine",
    "InferencePrimitive",
    "PrimitiveLibrary",
    "SETUP_PROMPT",
]
