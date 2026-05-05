"""
Skill Registry — Universal Discovery & Dispatch
================================================
Allows an AI Agent to discover, load, and route to any skill
using a single registry instance.

Usage:
    from skills.core import registry
    signal = await registry.dispatch("fomo_detector", {"symbol": "BTC/USDT"})
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

from skills.core.base import BaseSkill


class SkillRegistry:
    """Central registry for all MASTER Trading skills."""

    def __init__(self) -> None:
        self._skills: dict[str, BaseSkill] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    def register(self, skill: BaseSkill, override: bool = False) -> None:
        """Manually register a skill instance."""
        key = skill.name.lower()
        if key in self._skills and not override:
            raise KeyError(f"Skill '{key}' already registered. Use override=True to replace.")
        self._skills[key] = skill
        self._metadata[key] = {
            "description": skill.description,
            "version": skill.version,
            "triggers": skill.triggers,
            "class": skill.__class__.__name__,
        }

    def register_class(self, cls: type[BaseSkill], *args: Any, **kwargs: Any) -> None:
        """Instantiate and register a skill class."""
        instance = cls(*args, **kwargs)
        self.register(instance)

    def auto_discover(self, package_name: str = "skills") -> list[str]:
        """
        Auto-discover skills by scanning sub-packages for classes
        inheriting from BaseSkill.
        """
        discovered: list[str] = []
        try:
            package = importlib.import_module(package_name)
        except ImportError:
            return discovered

        for _, modname, ispkg in pkgutil.iter_modules(package.__path__, package_name + "."):
            if ispkg:
                continue
            try:
                mod = importlib.import_module(modname)
                for attr_name in dir(mod):
                    obj = getattr(mod, attr_name)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, BaseSkill)
                        and obj is not BaseSkill
                        and not getattr(obj, "__abstractmethods__", None)
                    ):
                        try:
                            self.register_class(obj)
                            discovered.append(obj.name)
                        except Exception:
                            pass
            except Exception:
                continue
        return discovered

    def get(self, name: str) -> BaseSkill | None:
        """Retrieve a skill by name (case-insensitive)."""
        return self._skills.get(name.lower())

    def list_skills(self) -> dict[str, dict[str, Any]]:
        """Return metadata for all registered skills."""
        return dict(self._metadata)

    def load(self, skill_id: str, config: dict[str, Any] | None = None) -> BaseSkill | None:
        """Discover and instantiate a skill by name with optional configuration."""
        key = skill_id.lower()
        if key in self._skills:
            return self._skills[key]

        import pkgutil

        for package in ["skills", "backtest"]:
            try:
                pkg = importlib.import_module(package)
            except Exception:
                continue
            for _, modname, ispkg in pkgutil.walk_packages(pkg.__path__, package + "."):
                if ispkg:
                    continue
                try:
                    mod = importlib.import_module(modname)
                except Exception:
                    continue
                for attr_name in dir(mod):
                    obj = getattr(mod, attr_name)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, BaseSkill)
                        and obj is not BaseSkill
                        and not getattr(obj, "__abstractmethods__", None)
                        and obj.name.lower() == key
                    ):
                        try:
                            instance = obj(**(config or {}))
                            self.register(instance)
                            return instance
                        except Exception:
                            pass
        return None

    async def start(self, name: str) -> None:
        """Start a loaded skill (lifecycle hook)."""
        skill = self.get(name)
        if skill is not None:
            await skill.start()

    async def stop(self, name: str) -> None:
        """Stop a loaded skill (lifecycle hook)."""
        skill = self.get(name)
        if skill is not None:
            await skill.stop()

    def health(self, name: str) -> dict[str, Any]:
        """Return health status for a loaded skill."""
        skill = self.get(name)
        if skill is not None:
            return skill.health()
        return {"status": "unknown", "skill": name}

    async def dispatch(self, name: str, context: dict[str, Any]) -> Any:
        """Execute a skill by name with the provided context."""
        skill = self.get(name)
        if skill is None:
            available = ", ".join(self._skills.keys())
            raise KeyError(f"Skill '{name}' not found. Available: {available}")
        return await skill.run(context)

    def __contains__(self, name: str) -> bool:
        return name.lower() in self._skills

    def __repr__(self) -> str:
        return f"<SkillRegistry skills={list(self._skills.keys())}>"


# Global singleton registry
registry = SkillRegistry()
