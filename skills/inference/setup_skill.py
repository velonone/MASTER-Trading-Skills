"""
CalibrationSetupSkill — Agent-Callable Calibration Configurator
================================================================
Exposes calibration source selection as a normal skill that an LLM
agent can dispatch through :class:`AgentToolAdapter`.

Recommended agent flow (also documented in SKILL.md):

    1. On first inference call, the engine resolves a calibration. If
       it falls back to the bundled snapshot, ``_meta.fallback`` is True
       and a hint is included.
    2. The agent SHOULD surface :data:`SETUP_PROMPT` to the user once,
       so the user can pick deliberately.
    3. The user replies with one of: snapshot / self / custom /
       placeholder (and a path when applicable).
    4. The agent calls this skill with that selection, which persists
       the choice to ``~/.master-trading/config.json``.
    5. Subsequent calls resolve the new source automatically.

Strict mode (``strict_calibration=True`` on the engine) escalates step
1 from a hint to a raised :class:`CalibrationNotConfigured`, forcing
the agent to complete setup before any inference happens. This is
appropriate for production deployments.
"""

from __future__ import annotations

from typing import Any

from skills.core.base import BaseSkill
from skills.inference.calibration import (
    SETUP_PROMPT,
    Calibration,
    CalibrationSource,
)


class CalibrationSetupSkill(BaseSkill):
    """
    Tool the agent calls AFTER asking the user which calibration source
    they want. Persists the choice and returns a short status payload
    the agent can echo back to the user.

    Expected context shape::

        {
            "action": "set" | "show" | "reset" | "prompt",
            "source": "snapshot" | "self" | "custom" | "placeholder",
            "path": "/abs/path/to/calibration.json"   # for custom/self
        }

    The default action is ``set`` when ``source`` is provided; otherwise
    the action defaults to ``show``.
    """

    name = "calibration_setup"
    description = (
        "Configure the inference calibration source (snapshot / self / "
        "custom / placeholder). Call this AFTER asking the user which "
        "source they want. Use action='prompt' to retrieve the exact "
        "text to show the user."
    )
    version = "1.0.0"
    triggers = ["calibration", "setup", "configure"]

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        action: str = (
            context.get("action") or ("set" if context.get("source") else "show")
        ).lower()

        if action == "prompt":
            return {"status": "ok", "prompt": SETUP_PROMPT}

        if action == "show":
            return {"status": "ok", "current": Calibration.show()}

        if action == "reset":
            removed = Calibration.reset()
            return {"status": "ok", "reset": removed}

        if action == "set":
            source = context.get("source")
            if not source:
                return {
                    "status": "error",
                    "code": "MISSING_SOURCE",
                    "message": "Provide source=<snapshot|self|custom|placeholder>",
                    "prompt": SETUP_PROMPT,
                }
            valid = {s.value for s in CalibrationSource}
            if source not in valid:
                return {
                    "status": "error",
                    "code": "INVALID_SOURCE",
                    "message": f"source must be one of {sorted(valid)}; got {source!r}",
                    "prompt": SETUP_PROMPT,
                }

            path: str | None = context.get("path")

            try:
                config_path = Calibration.persist_choice(source, path=path)
            except Exception as exc:  # noqa: BLE001
                return {
                    "status": "error",
                    "code": "PERSIST_FAILED",
                    "message": str(exc),
                }

            # Verify the choice resolves cleanly so the agent can confirm.
            try:
                resolved = Calibration.resolve()
                meta = resolved.emit_meta()
            except Exception as exc:  # noqa: BLE001
                return {
                    "status": "warning",
                    "code": "PERSISTED_BUT_UNRESOLVABLE",
                    "message": f"Saved choice but could not load it back: {exc}",
                    "config_path": str(config_path),
                }

            return {
                "status": "ok",
                "source": source,
                "config_path": str(config_path),
                "calibration": meta,
            }

        return {
            "status": "error",
            "code": "UNKNOWN_ACTION",
            "message": f"action must be set/show/reset/prompt; got {action!r}",
        }
