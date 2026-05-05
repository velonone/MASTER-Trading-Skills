"""
Tests for SkillPack metadata parser (P3).
"""

import tempfile
from pathlib import Path

from skills.core.skillpack import (
    discover_skillpacks,
    parse_skill_md,
)


def test_parse_skill_md_with_frontmatter():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("""---
name: test_pack
version: "1.2.3"
description: A test skill pack
author: VelonLabs
skills:
  - name: dummy_skill
    class: DummySkill
    module: skills.dummy
    description: Does nothing
    triggers: [test]
dependencies:
  - numpy
---

# Test Pack

This is the body.
""")
        f.flush()
        meta, body = parse_skill_md(Path(f.name))

    assert meta is not None
    assert meta.name == "test_pack"
    assert meta.version == "1.2.3"
    assert meta.author == "VelonLabs"
    assert len(meta.skills) == 1
    assert meta.skills[0].name == "dummy_skill"
    assert meta.skills[0].class_name == "DummySkill"
    assert meta.dependencies == ["numpy"]
    assert "# Test Pack" in body


def test_parse_skill_md_without_frontmatter():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("# Just Markdown\n\nNo frontmatter here.\n")
        f.flush()
        meta, body = parse_skill_md(Path(f.name))

    assert meta is None
    assert "Just Markdown" in body


def test_discover_skillpacks_finds_real_packs():
    """Discover should find the real SKILL.md files we created."""
    root = Path("skills")
    packs = discover_skillpacks(root)

    assert "signals_technical" in packs
    assert "execution_web3" in packs
    assert "adversarial" in packs

    signals_meta, _ = packs["signals_technical"]
    assert any(s.name == "order_book_imbalance" for s in signals_meta.skills)
    assert any(s.name == "funding_arbitrage" for s in signals_meta.skills)

    web3_meta, _ = packs["execution_web3"]
    assert any(s.name == "web3_dex_executor" for s in web3_meta.skills)
    assert "web3>=7.0" in web3_meta.dependencies


def test_skillpack_skills_have_triggers():
    root = Path("skills")
    packs = discover_skillpacks(root)
    meta, _ = packs["adversarial"]
    fomo = next(s for s in meta.skills if s.name == "fomo_detector")
    assert "fomo" in fomo.triggers
    assert "panic" in fomo.triggers
