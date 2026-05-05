"""
Agent Tool Adapter — Universal LLM Skill Router
================================================
Connects LLM tool-calling APIs to the MASTER Trading skill registry.
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from skills.agent.policy import AgentPolicy
from skills.agent.schema import SkillSchemaGenerator
from skills.core.base import BaseConnector, BaseRiskManager, BaseSkill, BaseStrategy
from skills.core.logging import get_logger
from skills.core.registry import SkillRegistry

_audit_logger = get_logger("agent.audit")


def _capability_for(skill: BaseSkill) -> str:
    """Map a skill instance to a coarse capability tier for policy gating."""
    if isinstance(skill, BaseConnector):
        return "trade"
    if isinstance(skill, BaseRiskManager):
        return "risk"
    if isinstance(skill, BaseStrategy):
        return "signal"
    return "read"


def _extract_notional(arguments: dict[str, Any]) -> Decimal:
    """
    Best-effort notional extraction from tool arguments. Supports flat args
    and nested {"context": {...}} envelopes used by single-param run() skills.
    """
    if not isinstance(arguments, dict):
        return Decimal("0")
    payload: dict[str, Any] = arguments
    if set(arguments.keys()) == {"context"} and isinstance(arguments["context"], dict):
        payload = arguments["context"]

    for key in ("notional", "amount_in", "quantity"):
        if key in payload and payload[key] is not None:
            try:
                return Decimal(str(payload[key]))
            except (InvalidOperation, ValueError, TypeError):
                continue

    order = payload.get("order")
    if isinstance(order, dict):
        for key in ("notional", "quantity"):
            if key in order and order[key] is not None:
                try:
                    return Decimal(str(order[key]))
                except (InvalidOperation, ValueError, TypeError):
                    continue
    return Decimal("0")


class AgentToolAdapter:
    """
    Wraps all registered skills as LLM-callable tools.

    Pass an :class:`AgentPolicy` to gate every dispatch with capability,
    blocklist, and budget checks. Without a policy the adapter behaves as
    before (open dispatch). Every dispatch is recorded in an in-memory
    audit log and emitted via :mod:`skills.core.logging`.
    """

    def __init__(self, registry: SkillRegistry, policy: AgentPolicy | None = None):
        self.registry = registry
        self.policy = policy
        self.audit_log: list[dict[str, Any]] = []
        self._schemas: list[dict[str, Any]] = []
        self._build_schemas()

    def _build_schemas(self) -> None:
        """Auto-generate schemas for all registered skills."""
        for name, skill in self.registry._skills.items():
            schema = SkillSchemaGenerator.from_callable(skill.run, name=name)
            schema["function"]["description"] = (
                skill.description or schema["function"]["description"]
            )
            self._schemas.append(schema)

    def export_openai_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions for OpenAI Chat Completions API."""
        return self._schemas

    def export_anthropic_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions for Anthropic Messages API."""
        return [
            {
                "name": s["function"]["name"],
                "description": s["function"]["description"],
                "input_schema": s["function"]["parameters"],
            }
            for s in self._schemas
        ]

    def _validate_arguments(self, tool_name: str, arguments: dict[str, Any]) -> str | None:
        """Pre-validate LLM arguments against the tool's JSONSchema."""
        schema = next((s for s in self._schemas if s["function"]["name"] == tool_name), None)
        if schema is None:
            return None

        params = schema["function"].get("parameters", {})
        required = params.get("required", [])
        properties = params.get("properties", {})

        # Single-param 'context' skills: arguments dict IS the context.
        if set(properties.keys()) == {"context"}:
            return None

        for field in required:
            if field not in arguments:
                return f"Missing required field: '{field}'"

        for key, value in arguments.items():
            prop = properties.get(key, {})
            expected_type = prop.get("type")
            if expected_type == "string" and not isinstance(value, str):
                return f"Field '{key}' must be a string"
            if expected_type == "integer" and not isinstance(value, int):
                return f"Field '{key}' must be an integer"
            if expected_type == "number" and not isinstance(value, (int, float)):
                return f"Field '{key}' must be a number"
            if expected_type == "boolean" and not isinstance(value, bool):
                return f"Field '{key}' must be a boolean"
            if expected_type == "array" and not isinstance(value, list):
                return f"Field '{key}' must be an array"

        return None

    def _record_audit(self, entry: dict[str, Any]) -> None:
        """Append an audit entry and emit via the structured logger."""
        self.audit_log.append(entry)
        try:
            _audit_logger.info(json.dumps(entry, default=str))
        except Exception:
            pass

    async def dispatch(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a tool call from an LLM with policy gate, pre-validation,
        and structured errors.

        Returns:
            {"status": "success", "result": ...}
            or
            {"status": "error", "code": <CODE>, "message": ...}
            where CODE is one of: SKILL_NOT_FOUND, POLICY_DENIED,
            BUDGET_EXCEEDED, VALIDATION_ERROR, EXECUTION_ERROR.
        """
        ts = datetime.utcnow().isoformat()
        skill = self.registry.get(tool_name)
        if skill is None:
            response = {
                "status": "error",
                "code": "SKILL_NOT_FOUND",
                "message": f"Skill '{tool_name}' not found.",
                "available": list(self.registry.list_skills().keys()),
            }
            self._record_audit(
                {
                    "ts": ts,
                    "tool": tool_name,
                    "outcome": "skill_not_found",
                }
            )
            return response

        capability = _capability_for(skill)
        notional = _extract_notional(arguments)

        if self.policy is not None:
            allowed, reason = self.policy.can_invoke(tool_name, capability)
            if not allowed:
                self._record_audit(
                    {
                        "ts": ts,
                        "tool": tool_name,
                        "capability": capability,
                        "outcome": "policy_denied",
                        "reason": reason,
                    }
                )
                return {
                    "status": "error",
                    "code": "POLICY_DENIED",
                    "message": reason or "Policy denied invocation",
                    "tool": tool_name,
                    "capability": capability,
                }

            budget_ok, budget_reason = self.policy.check_budget(tool_name, notional)
            if not budget_ok:
                self._record_audit(
                    {
                        "ts": ts,
                        "tool": tool_name,
                        "capability": capability,
                        "notional": str(notional),
                        "outcome": "budget_exceeded",
                        "reason": budget_reason,
                    }
                )
                return {
                    "status": "error",
                    "code": "BUDGET_EXCEEDED",
                    "message": budget_reason or "Budget exceeded",
                    "tool": tool_name,
                    "notional": str(notional),
                }

        validation_error = self._validate_arguments(tool_name, arguments)
        if validation_error:
            self._record_audit(
                {
                    "ts": ts,
                    "tool": tool_name,
                    "outcome": "validation_error",
                    "reason": validation_error,
                }
            )
            return {
                "status": "error",
                "code": "VALIDATION_ERROR",
                "message": validation_error,
            }

        try:
            run_args = arguments
            schema = next((s for s in self._schemas if s["function"]["name"] == tool_name), None)
            if schema:
                properties = schema["function"].get("parameters", {}).get("properties", {})
                if set(properties.keys()) == {"context"} and "context" in arguments:
                    run_args = arguments["context"]
            result = await skill.run(run_args)
            if self.policy is not None and notional > 0 and capability == "trade":
                self.policy.record_spend(tool_name, notional)
            self._record_audit(
                {
                    "ts": ts,
                    "tool": tool_name,
                    "capability": capability,
                    "notional": str(notional),
                    "outcome": "success",
                }
            )
            return self._format_result(result)
        except Exception as exc:
            self._record_audit(
                {
                    "ts": ts,
                    "tool": tool_name,
                    "capability": capability,
                    "outcome": "execution_error",
                    "reason": str(exc),
                }
            )
            return {
                "status": "error",
                "code": "EXECUTION_ERROR",
                "message": str(exc),
                "skill": tool_name,
            }

    def _format_result(self, result: Any) -> dict[str, Any]:
        """Truncate and format results for LLM consumption."""
        payload = {"status": "success", "result": result}
        json_str = json.dumps(payload, default=str)
        if len(json_str) > 16000:
            truncated = json.dumps(
                {
                    "status": "success",
                    "result": str(result)[:8000] + "... [truncated]",
                }
            )
            return json.loads(truncated)
        return json.loads(json_str)

    def list_tools(self) -> list[str]:
        """Return human-readable tool list."""
        return [s["function"]["name"] for s in self._schemas]
