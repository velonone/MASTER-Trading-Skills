"""
Unit tests for skills.inference — Higher-Order Reasoning Engine.
"""

import pytest

from skills.core.types import EventCategory
from skills.inference import HigherOrderInferenceEngine, PrimitiveLibrary


@pytest.fixture
def engine():
    return HigherOrderInferenceEngine()


def test_primitive_library_defaults():
    lib = PrimitiveLibrary.default_library()
    assert "whale_exchange_deposit" in lib.primitives
    assert lib.get("yield_compression").base_confidence == 0.85


def test_singularity_detection_low(engine):
    result = engine.detect_singularity({"affects_core_assets": False, "magnitude": "small"})
    assert result["is_singularity"] is False
    assert result["score"] < 0.5


def test_singularity_detection_high(engine):
    result = engine.detect_singularity(
        {
            "affects_core_assets": True,
            "is_public": False,
            "has_leverage_exposure": True,
            "magnitude": "extreme",
        }
    )
    assert result["is_singularity"] is True
    assert result["score"] > 0.5


def test_causal_chain_whale_deposit(engine):
    chain = engine.build_causal_chain(
        "Whale deposits 5000 ETH to exchange", EventCategory.WHALE_MOVEMENT
    )
    assert len(chain.effects) >= 3
    assert (
        "bearish" in chain.convergence
        or "neutral" in chain.convergence
        or "uncertain" in chain.convergence
    )
    assert 0.0 <= chain.overall_confidence <= 1.0


def test_causal_chain_hack(engine):
    chain = engine.build_causal_chain("Protocol hacked for $50M", EventCategory.HACK_EXPLOIT)
    directions = [e.direction for e in chain.effects]
    assert "bearish" in directions


def test_prediction_generation(engine):
    pred = engine.generate_prediction("Coinbase lists TOKEN", EventCategory.LISTING)
    assert "causal_chain" in pred
    assert "signal_action" in pred
    assert pred["overall_confidence"] > 0.0


def test_backward_induction(engine):
    steps = engine.backward_induction("Maximize profit", ["Limited capital"])
    assert len(steps) > 0
    assert "Exit" in steps[-1] or "exit" in steps[-1]


def test_primitive_accuracy_update():
    lib = PrimitiveLibrary.default_library()
    p = lib.get("whale_exchange_deposit")
    p.record_outcome(was_correct=True)
    assert p.times_used == 1
    assert p.accuracy == 1.0
    p.record_outcome(was_correct=False)
    assert p.accuracy == 0.5


def test_underperformers():
    lib = PrimitiveLibrary.default_library()
    lib.primitives["test_bad"] = lib.primitives["whale_exchange_deposit"].model_copy()
    lib.primitives["test_bad"].name = "test_bad"
    for _ in range(10):
        lib.primitives["test_bad"].record_outcome(was_correct=False)
    bad = lib.underperformers(min_uses=5, threshold=0.4)
    assert any(p.name == "test_bad" for p in bad)
