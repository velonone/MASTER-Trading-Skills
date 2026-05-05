"""
Unit tests for SkillRegistry — discovery, loading, and dispatch.
"""

import pytest

from skills.core.registry import SkillRegistry


@pytest.mark.asyncio
async def test_registry_load_without_config():
    """Load should discover and instantiate a skill by name without configuration."""
    registry = SkillRegistry()
    skill = registry.load("fomo_detector")
    assert skill is not None
    assert skill.name == "fomo_detector"


@pytest.mark.asyncio
async def test_registry_load_with_config():
    """Load should pass configuration to skills requiring constructor arguments."""
    registry = SkillRegistry()
    skill = registry.load("whale_tracker", config={"etherscan_api_key": "dummy_key"})
    assert skill is not None
    assert skill.name == "whale_tracker"
    assert skill.etherscan_api_key == "dummy_key"


@pytest.mark.asyncio
async def test_registry_lifecycle_hooks():
    """Registry should proxy start/stop/health to loaded skills."""
    registry = SkillRegistry()
    skill = registry.load("fomo_detector")
    assert skill is not None

    await registry.start("fomo_detector")
    health = registry.health("fomo_detector")
    assert health["status"] == "ok"
    assert health["skill"] == "fomo_detector"
    await registry.stop("fomo_detector")
