"""
Unit tests for the Calibration resolver and CalibrationSetupSkill.

The Calibration system has three load paths (kwarg / env / config file)
plus a default snapshot fallback, and one strict-mode escape hatch that
raises CalibrationNotConfigured. These tests pin down the resolution
order and the agent-facing setup skill behaviour.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest import mock

import pytest

from skills.inference.calibration import (
    CONFIG_PATH,
    ENV_VAR,
    Calibration,
    CalibrationNotConfigured,
    CalibrationSource,
    SETUP_PROMPT,
)
from skills.inference.engine import HigherOrderInferenceEngine
from skills.inference.setup_skill import CalibrationSetupSkill
from skills.core.types import EventCategory


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """
    Redirect CONFIG_PATH to a tmp dir and clear MASTER_TRADING_* env so
    each test starts with a clean resolver state.
    """
    cfg_dir = tmp_path / ".master-trading"
    cfg_path = cfg_dir / "config.json"
    monkeypatch.setattr("skills.inference.calibration.CONFIG_DIR", cfg_dir)
    monkeypatch.setattr("skills.inference.calibration.CONFIG_PATH", cfg_path)
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.delenv("MASTER_TRADING_CALIBRATION_PATH", raising=False)
    return cfg_path


# ---------------------------------------------------------------------------
# Snapshot data integrity
# ---------------------------------------------------------------------------


def test_snapshot_contains_all_required_sections():
    cal = Calibration.velonlabs_snapshot()
    for key in ("primitives", "causal_chains", "singularity_weights",
                "signal_thresholds", "convergence_ratios"):
        assert key in cal.data, f"snapshot missing {key}"


def test_snapshot_provenance_metadata_is_real():
    """Snapshot must declare version, release date, and attribution."""
    cal = Calibration.velonlabs_snapshot()
    meta = cal.emit_meta()
    assert meta["calibration_source"] == "snapshot"
    assert meta["calibration_version"] == "2026.05"
    assert meta["calibration_released_at"]
    assert "VelonLabs" in meta["attribution"]


def test_snapshot_values_are_real_not_placeholder():
    """
    The point of the snapshot is that it ships real calibrated values,
    not 0.5 across the board. Confirm that primitives carry distinct,
    non-trivial confidences.
    """
    cal = Calibration.velonlabs_snapshot()
    confidences = {p["base_confidence"] for p in cal.data["primitives"].values()}
    assert len(confidences) > 1, "all primitives have identical confidence — looks like placeholder"
    assert any(c != 0.5 for c in confidences), "every confidence is 0.5 — looks like placeholder"


# ---------------------------------------------------------------------------
# Placeholder mode
# ---------------------------------------------------------------------------


def test_placeholder_clamps_all_confidences_to_half():
    cal = Calibration.placeholder()
    for prim in cal.data["primitives"].values():
        assert prim["base_confidence"] == 0.5
    for chain in cal.data["causal_chains"].values():
        for step in chain:
            assert step["confidence"] == 0.5


# ---------------------------------------------------------------------------
# Resolution order
# ---------------------------------------------------------------------------


def test_resolve_falls_back_to_snapshot_with_hint(isolated_config):
    cal = Calibration.resolve()
    assert cal.source == "snapshot"
    assert cal.meta.get("fallback") is True
    assert "hint" in cal.meta


def test_env_var_overrides_default(isolated_config, monkeypatch):
    monkeypatch.setenv(ENV_VAR, "placeholder")
    cal = Calibration.resolve()
    assert cal.source == "placeholder"
    # Placeholder is an explicit choice, not a fallback.
    assert cal.meta.get("fallback") is not True


def test_config_file_used_when_no_env(isolated_config):
    Calibration.persist_choice("snapshot")
    cal = Calibration.resolve()
    assert cal.source == "snapshot"
    assert cal.meta.get("fallback") is not True


def test_env_var_takes_precedence_over_config(isolated_config, monkeypatch):
    Calibration.persist_choice("snapshot")
    monkeypatch.setenv(ENV_VAR, "placeholder")
    cal = Calibration.resolve()
    assert cal.source == "placeholder"


def test_explicit_kwarg_takes_precedence_over_everything(isolated_config, monkeypatch):
    monkeypatch.setenv(ENV_VAR, "placeholder")
    Calibration.persist_choice("snapshot")
    explicit = Calibration.placeholder()
    cal = Calibration.resolve(explicit=explicit)
    assert cal is explicit


# ---------------------------------------------------------------------------
# Strict mode
# ---------------------------------------------------------------------------


def test_strict_mode_raises_when_unconfigured(isolated_config):
    with pytest.raises(CalibrationNotConfigured) as excinfo:
        Calibration.resolve(strict=True)
    assert "calibration source" in str(excinfo.value).lower()


def test_strict_mode_succeeds_with_env(isolated_config, monkeypatch):
    monkeypatch.setenv(ENV_VAR, "snapshot")
    cal = Calibration.resolve(strict=True)
    assert cal.source == "snapshot"


# ---------------------------------------------------------------------------
# Custom file source
# ---------------------------------------------------------------------------


def test_custom_source_loads_user_json(isolated_config, tmp_path):
    custom = tmp_path / "custom.json"
    snapshot = Calibration.velonlabs_snapshot().data
    snapshot["version"] = "user.0001"
    snapshot["source"] = "custom"
    custom.write_text(json.dumps(snapshot), encoding="utf-8")

    cal = Calibration.from_file(custom)
    assert cal.version == "user.0001"
    assert cal.source == "custom"


def test_custom_source_rejects_malformed_json(isolated_config, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"primitives": {}}), encoding="utf-8")  # missing other keys
    with pytest.raises(ValueError, match="missing required keys"):
        Calibration.from_file(bad)


# ---------------------------------------------------------------------------
# Freshness warning
# ---------------------------------------------------------------------------


def test_freshness_warning_triggers_after_threshold(isolated_config):
    """A snapshot that's been around longer than FRESHNESS_WARN_DAYS warns."""
    cal = Calibration.velonlabs_snapshot()
    cal.data["released_at"] = "2020-01-01"
    warning = cal.freshness_warning()
    assert warning is not None
    assert "calibration is" in warning.lower()


def test_recent_snapshot_emits_no_warning():
    cal = Calibration.velonlabs_snapshot()
    # Default snapshot's released_at is recent w.r.t. today's date.
    assert cal.freshness_warning() is None


# ---------------------------------------------------------------------------
# Engine integrates calibration
# ---------------------------------------------------------------------------


def test_engine_default_uses_resolved_calibration(isolated_config):
    engine = HigherOrderInferenceEngine()
    assert engine.calibration.source == "snapshot"
    pred = engine.generate_prediction(
        "Whale 0xabc deposited 5000 ETH to Binance",
        EventCategory.WHALE_MOVEMENT,
    )
    # Provenance must travel into the prediction output for audit.
    assert pred["_meta"]["calibration_source"] == "snapshot"
    assert pred["_meta"]["calibration_version"] == "2026.05"


def test_engine_accepts_explicit_calibration(isolated_config):
    engine = HigherOrderInferenceEngine(calibration=Calibration.placeholder())
    pred = engine.generate_prediction(
        "Whale 0xabc deposited 5000 ETH to Binance",
        EventCategory.WHALE_MOVEMENT,
    )
    assert pred["_meta"]["calibration_source"] == "placeholder"
    # In placeholder mode, every chain step is 0.5 → overall confidence
    # is much smaller than under the real snapshot.
    assert pred["overall_confidence"] < 0.5


def test_engine_strict_mode_raises_without_config(isolated_config):
    with pytest.raises(CalibrationNotConfigured):
        HigherOrderInferenceEngine(strict_calibration=True)


# ---------------------------------------------------------------------------
# Agent setup skill
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_setup_skill_returns_prompt_for_agent(isolated_config):
    skill = CalibrationSetupSkill()
    result = await skill.run({"action": "prompt"})
    assert result["status"] == "ok"
    assert result["prompt"] == SETUP_PROMPT


@pytest.mark.asyncio
async def test_setup_skill_persists_choice(isolated_config):
    skill = CalibrationSetupSkill()
    result = await skill.run({"source": "snapshot"})
    assert result["status"] == "ok"
    assert result["source"] == "snapshot"
    assert Path(result["config_path"]).exists()
    # Resolution after persist should not be a fallback.
    cal = Calibration.resolve()
    assert cal.meta.get("fallback") is not True


@pytest.mark.asyncio
async def test_setup_skill_rejects_invalid_source(isolated_config):
    skill = CalibrationSetupSkill()
    result = await skill.run({"source": "garbage"})
    assert result["status"] == "error"
    assert result["code"] == "INVALID_SOURCE"
    assert "prompt" in result  # always offer the prompt back so agent can recover


@pytest.mark.asyncio
async def test_setup_skill_show_returns_resolution_state(isolated_config):
    skill = CalibrationSetupSkill()
    result = await skill.run({"action": "show"})
    assert result["status"] == "ok"
    assert "current" in result
    assert result["current"]["resolved"]["calibration_source"] == "snapshot"


@pytest.mark.asyncio
async def test_setup_skill_reset_clears_persisted_config(isolated_config):
    Calibration.persist_choice("snapshot")
    skill = CalibrationSetupSkill()
    result = await skill.run({"action": "reset"})
    assert result["status"] == "ok"
    assert result["reset"] is True


# ---------------------------------------------------------------------------
# Setup prompt content sanity
# ---------------------------------------------------------------------------


def test_setup_prompt_lists_all_real_sources():
    """The prompt must mention every source the resolver actually accepts."""
    for source in CalibrationSource:
        assert source.value in SETUP_PROMPT, f"prompt missing {source.value}"
