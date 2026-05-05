"""
Agent Policy — Capability & Budget Controls
============================================
Defines what an LLM agent is allowed to do and how much it can spend.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Dict, Optional, Set


class AgentPolicy:
    """
    Access-control envelope for LLM tool dispatch.

    Example:
        policy = AgentPolicy(
            capabilities={"read", "signal"},          # no "trade"
            daily_budget=Decimal("500"),
            blocked_skills={"web3_dex_executor"},
        )
    """

    def __init__(
        self,
        capabilities: Optional[Set[str]] = None,
        daily_budget: Optional[Decimal] = None,
        blocked_skills: Optional[Set[str]] = None,
        skill_budgets: Optional[Dict[str, Decimal]] = None,
    ):
        self.capabilities = capabilities or {"read"}
        self.daily_budget = daily_budget
        self.blocked_skills = set(blocked_skills or [])
        self.skill_budgets = skill_budgets or {}

        self._daily_spent: Decimal = Decimal("0")
        self._skill_spent: Dict[str, Decimal] = {}

    def can_invoke(self, skill_name: str, capability: str) -> tuple[bool, Optional[str]]:
        """
        Check whether *skill_name* can be invoked under *capability*.
        Returns (allowed, reason_or_none).
        """
        if skill_name in self.blocked_skills:
            return False, f"Skill '{skill_name}' is blocked by policy"

        if capability not in self.capabilities:
            return False, f"Capability '{capability}' not granted (have: {self.capabilities})"

        return True, None

    def check_budget(self, skill_name: str, notional: Decimal = Decimal("0")) -> tuple[bool, Optional[str]]:
        """
        Check if spending *notional* would exceed budget.
        Returns (allowed, reason_or_none).
        """
        if self.daily_budget is not None:
            if self._daily_spent + notional > self.daily_budget:
                return False, (
                    f"Daily budget exceeded: {self._daily_spent + notional} > {self.daily_budget}"
                )

        skill_limit = self.skill_budgets.get(skill_name)
        if skill_limit is not None:
            skill_spent = self._skill_spent.get(skill_name, Decimal("0"))
            if skill_spent + notional > skill_limit:
                return False, (
                    f"Skill budget exceeded for '{skill_name}': {skill_spent + notional} > {skill_limit}"
                )

        return True, None

    def record_spend(self, skill_name: str, notional: Decimal) -> None:
        """Record a spend against budget trackers."""
        self._daily_spent += notional
        self._skill_spent[skill_name] = self._skill_spent.get(skill_name, Decimal("0")) + notional

    @classmethod
    def read_only(cls) -> "AgentPolicy":
        """Convenience factory for a read-only agent."""
        return cls(capabilities={"read"})

    @classmethod
    def signal_only(cls) -> "AgentPolicy":
        """Convenience factory for signal generation only."""
        return cls(capabilities={"read", "signal"})

    @classmethod
    def full_trading(cls, daily_budget: Decimal = Decimal("1000")) -> "AgentPolicy":
        """Convenience factory for a trading agent with budget cap."""
        return cls(
            capabilities={"read", "signal", "trade"},
            daily_budget=daily_budget,
        )
