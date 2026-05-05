"""
LLM Agent Tool Adapter — Multi-Provider Function Calling
=========================================================
Exposes every MASTER Trading skill as standardized tools for:
- OpenAI Functions
- Anthropic Tool Use
- AutoGPT / Local LLMs

Features:
- Automatic JSON Schema generation from Pydantic models
- Context-window truncation guards
- Unified dispatch router
"""

from skills.agent.adapter import AgentToolAdapter
from skills.agent.policy import AgentPolicy
from skills.agent.schema import SkillSchemaGenerator

__all__ = [
    "AgentToolAdapter",
    "AgentPolicy",
    "SkillSchemaGenerator",
]
