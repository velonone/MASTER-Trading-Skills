"""
LLM Agent Tool Adapter — Multi-Provider Tool Use
=================================================
Exposes every MASTER Trading skill as a standardized tool for the major
agent runtimes:

- Anthropic Messages API (Claude Code, Cursor, Cline, Windsurf)
- OpenAI Responses / Chat Completions (Codex, Copilot)
- Moonshot Kimi tools (Kimi Code)
- Local / self-hosted runtimes via the same JSON Schema

Features:
- Automatic JSON Schema generation from Pydantic models
- Capability + budget gate enforced before every dispatch
- Per-call audit log
- Context-window truncation guards
"""

from skills.agent.adapter import AgentToolAdapter
from skills.agent.policy import AgentPolicy
from skills.agent.schema import SkillSchemaGenerator

__all__ = [
    "AgentToolAdapter",
    "AgentPolicy",
    "SkillSchemaGenerator",
]
