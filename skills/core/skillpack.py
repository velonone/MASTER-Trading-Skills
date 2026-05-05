"""
SkillPack — BofAI-style metadata parser for self-contained skills.
===================================================================
Parses YAML-frontmatter SKILL.md files into structured metadata.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


try:
    import yaml

    _YAML_OK = True
except ImportError:  # pragma: no cover
    _YAML_OK = False


class SkillEntry(BaseModel):
    """Individual skill within a SkillPack."""
    name: str
    class_name: str = Field(alias="class")
    module: str
    description: str = ""
    triggers: List[str] = Field(default_factory=list)


class SkillPackMetadata(BaseModel):
    """Top-level metadata from a SKILL.md frontmatter block."""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: Optional[str] = None
    skills: List[SkillEntry] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)


def parse_skill_md(path: Path) -> Tuple[Optional[SkillPackMetadata], str]:
    """
    Parse a SKILL.md file.

    Returns:
        (metadata, body) where metadata is None if no frontmatter is found.
    """
    text = path.read_text(encoding="utf-8")

    # YAML frontmatter: ---\n...\n---
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not match:
        return None, text.strip()

    if not _YAML_OK:
        raise RuntimeError("PyYAML is required to parse SKILL.md frontmatter")

    frontmatter = yaml.safe_load(match.group(1))
    body = match.group(2).strip()
    metadata = SkillPackMetadata(**frontmatter)
    return metadata, body


def discover_skillpacks(root: Path) -> Dict[str, Tuple[SkillPackMetadata, str]]:
    """
    Recursively discover all SKILL.md files under *root*.

    Returns:
        Mapping of pack name -> (metadata, body).
    """
    packs: Dict[str, Tuple[SkillPackMetadata, str]] = {}
    for skill_md in root.rglob("SKILL.md"):
        try:
            meta, body = parse_skill_md(skill_md)
            if meta:
                packs[meta.name] = (meta, body)
        except Exception:
            continue
    return packs
