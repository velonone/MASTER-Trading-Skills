"""
Unit tests for LLM Agent Tool Adapter.
"""

from decimal import Decimal

import pytest

from skills.adversarial.sentiment import FOMODetector
from skills.agent import AgentPolicy, AgentToolAdapter, SkillSchemaGenerator
from skills.core.base import BaseConnector, BaseSkill
from skills.core.registry import SkillRegistry
from skills.core.types import ExecutionReport, Order


def test_schema_from_callable():
    def sample_func(symbol: str, threshold: float = 0.5) -> dict:
        """Sample function for schema generation."""
        return {"symbol": symbol}

    schema = SkillSchemaGenerator.from_callable(sample_func, name="sample_tool")
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "sample_tool"
    assert "symbol" in schema["function"]["parameters"]["properties"]
    assert "symbol" in schema["function"]["parameters"]["required"]
    assert "threshold" not in schema["function"]["parameters"]["required"]


def test_schema_types():
    assert SkillSchemaGenerator._python_type_to_json(int)["type"] == "integer"
    assert SkillSchemaGenerator._python_type_to_json(float)["type"] == "number"
    assert SkillSchemaGenerator._python_type_to_json(bool)["type"] == "boolean"
    assert SkillSchemaGenerator._python_type_to_json(str)["type"] == "string"
    assert SkillSchemaGenerator._python_type_to_json(list)["type"] == "array"


def test_schema_optional_collapses_to_inner_type():
    """Optional[int] must yield integer with nullable=True, not a dropped string."""
    from typing import Optional

    # ruff UP045 suggests `int | None`, but the explicit `Optional[int]` form
    # is the subject under test — the schema generator must handle both.
    schema = SkillSchemaGenerator._python_type_to_json(Optional[int])  # noqa: UP045
    assert schema["type"] == "integer"
    assert schema.get("nullable") is True


def test_schema_decimal_is_number():
    """Decimal must map to number, not string."""
    schema = SkillSchemaGenerator._python_type_to_json(Decimal)
    assert schema["type"] == "number"


def test_schema_literal_is_enum():
    """Literal[\"BUY\", \"SELL\"] must produce an enum, not a bare string."""
    from typing import Literal as Lit

    schema = SkillSchemaGenerator._python_type_to_json(Lit["BUY", "SELL"])
    assert schema["type"] == "string"
    assert schema["enum"] == ["BUY", "SELL"]


def test_schema_enum_class_is_enum():
    """Enum subclasses must produce an enum schema with member values."""
    import enum

    class Colour(str, enum.Enum):
        RED = "RED"
        GREEN = "GREEN"

    schema = SkillSchemaGenerator._python_type_to_json(Colour)
    assert schema["enum"] == ["RED", "GREEN"]
    assert schema["type"] == "string"


def test_schema_typed_list_preserves_item_type():
    """List[int] must produce array<integer>, not array<string>."""
    schema = SkillSchemaGenerator._python_type_to_json(list[int])
    assert schema["type"] == "array"
    assert schema["items"]["type"] == "integer"


def test_adapter_exports_openai_tools():
    registry = SkillRegistry()
    registry.register(FOMODetector())
    adapter = AgentToolAdapter(registry)
    tools = adapter.export_openai_tools()
    assert len(tools) > 0
    assert tools[0]["type"] == "function"
    assert "parameters" in tools[0]["function"]


def test_adapter_exports_anthropic_tools():
    registry = SkillRegistry()
    registry.register(FOMODetector())
    adapter = AgentToolAdapter(registry)
    tools = adapter.export_anthropic_tools()
    assert len(tools) > 0
    assert "input_schema" in tools[0]


@pytest.mark.asyncio
async def test_adapter_dispatch():
    registry = SkillRegistry()
    registry.register(FOMODetector())
    adapter = AgentToolAdapter(registry)
    result = await adapter.dispatch(
        "fomo_detector",
        {
            "symbol": "BTC/USDT",
            "prices": [50000, 52000, 55000],
            "volumes": [100, 500, 1000],
        },
    )
    assert "result" in result or "error" in result


def test_adapter_list_tools():
    registry = SkillRegistry()
    registry.register(FOMODetector())
    adapter = AgentToolAdapter(registry)
    names = adapter.list_tools()
    assert "fomo_detector" in names


@pytest.mark.asyncio
async def test_adapter_dispatch_skill_not_found():
    """Dispatching an unregistered skill returns structured SKILL_NOT_FOUND error."""
    registry = SkillRegistry()
    adapter = AgentToolAdapter(registry)
    result = await adapter.dispatch("nonexistent_skill", {})
    assert result["status"] == "error"
    assert result["code"] == "SKILL_NOT_FOUND"
    assert "nonexistent_skill" in result["message"]


@pytest.mark.asyncio
async def test_adapter_dispatch_success():
    """Dispatching a valid skill with valid arguments returns status: success."""
    registry = SkillRegistry()
    registry.register(FOMODetector())
    adapter = AgentToolAdapter(registry)
    result = await adapter.dispatch(
        "fomo_detector",
        {
            "symbol": "BTC/USDT",
            "prices": [50000, 52000],
            "volumes": [100, 500],
        },
    )
    assert result["status"] == "success"
    assert "result" in result


@pytest.mark.asyncio
async def test_adapter_dispatch_validation_error():
    """Dispatching with missing required arguments returns VALIDATION_ERROR."""

    class ValidatedSkill(BaseSkill):
        name = "validated"

        async def run(self, symbol: str, threshold: float = 0.5) -> dict:
            return {"symbol": symbol}

    registry = SkillRegistry()
    registry.register(ValidatedSkill())
    adapter = AgentToolAdapter(registry)
    result = await adapter.dispatch(
        "validated",
        {
            # Missing required 'symbol'
        },
    )
    assert result["status"] == "error"
    assert result["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_adapter_dispatch_execution_error():
    """Skill raising an exception returns structured EXECUTION_ERROR."""
    registry = SkillRegistry()

    class BrokenSkill(BaseSkill):
        name = "broken"

        async def run(self, context):
            raise RuntimeError("intentional failure")

    registry.register(BrokenSkill())
    adapter = AgentToolAdapter(registry)
    result = await adapter.dispatch("broken", {})
    assert result["status"] == "error"
    assert result["code"] == "EXECUTION_ERROR"
    assert "intentional failure" in result["message"]


def test_format_result_truncation():
    registry = SkillRegistry()
    adapter = AgentToolAdapter(registry)
    big_result = "x" * 20000
    formatted = adapter._format_result(big_result)
    assert "truncated" in str(formatted) or len(str(formatted)) < 20000


# ---------------------------------------------------------------------------
# Policy gate (P0): capability + blocklist + budget enforcement
# ---------------------------------------------------------------------------


class _FakeConnector(BaseConnector):
    """Trade-capability skill used to exercise policy gating."""

    name = "fake_connector"
    description = "test trade connector"
    venue = "test"

    async def fetch_ohlcv(self, symbol, timeframe="1h", limit=100):
        return []

    async def place_order(self, order):
        return ExecutionReport(order=order, status="FILLED", total_filled=order.quantity)

    async def cancel_order(self, order_id, symbol):
        return ExecutionReport(
            order=Order(symbol=symbol, side="SELL", order_type="MARKET", quantity=Decimal("0")),
            status="CANCELLED",
        )

    async def fetch_position(self, symbol):
        return None

    async def run(self, context):
        return {"executed": True, "amount_in": context.get("amount_in", 0)}


@pytest.mark.asyncio
async def test_policy_blocks_when_capability_missing():
    """Read-only policy must reject a trade-tier skill."""
    registry = SkillRegistry()
    registry.register(_FakeConnector())
    adapter = AgentToolAdapter(registry, policy=AgentPolicy.read_only())
    result = await adapter.dispatch("fake_connector", {"context": {"amount_in": 10}})
    assert result["status"] == "error"
    assert result["code"] == "POLICY_DENIED"
    assert adapter.audit_log[-1]["outcome"] == "policy_denied"


@pytest.mark.asyncio
async def test_policy_blocks_blocked_skill():
    """Explicit blocklist takes precedence even when capability is granted."""
    registry = SkillRegistry()
    registry.register(_FakeConnector())
    policy = AgentPolicy(
        capabilities={"read", "signal", "trade"},
        blocked_skills={"fake_connector"},
    )
    adapter = AgentToolAdapter(registry, policy=policy)
    result = await adapter.dispatch("fake_connector", {"context": {"amount_in": 10}})
    assert result["status"] == "error"
    assert result["code"] == "POLICY_DENIED"
    assert "blocked" in result["message"].lower()


@pytest.mark.asyncio
async def test_policy_enforces_daily_budget():
    """Daily budget cap rejects the call before skill execution."""
    registry = SkillRegistry()
    registry.register(_FakeConnector())
    policy = AgentPolicy.full_trading(daily_budget=Decimal("100"))
    adapter = AgentToolAdapter(registry, policy=policy)

    first = await adapter.dispatch("fake_connector", {"context": {"amount_in": "60"}})
    assert first["status"] == "success"

    second = await adapter.dispatch("fake_connector", {"context": {"amount_in": "60"}})
    assert second["status"] == "error"
    assert second["code"] == "BUDGET_EXCEEDED"


@pytest.mark.asyncio
async def test_policy_allows_signal_skill():
    """Signal-only policy must allow signal-tier skills."""
    registry = SkillRegistry()
    registry.register(FOMODetector())
    adapter = AgentToolAdapter(registry, policy=AgentPolicy.signal_only())
    result = await adapter.dispatch(
        "fomo_detector",
        {
            "symbol": "BTC/USDT",
            "prices": [50000, 52000, 55000],
            "volumes": [100, 500, 1000],
        },
    )
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_audit_log_records_every_dispatch():
    """Every dispatch path appends an audit entry."""
    registry = SkillRegistry()
    registry.register(FOMODetector())
    adapter = AgentToolAdapter(registry)

    await adapter.dispatch("nonexistent", {})
    await adapter.dispatch(
        "fomo_detector",
        {
            "symbol": "BTC/USDT",
            "prices": [50000, 52000],
            "volumes": [100, 500],
        },
    )

    assert len(adapter.audit_log) == 2
    assert adapter.audit_log[0]["outcome"] == "skill_not_found"
    assert adapter.audit_log[1]["outcome"] == "success"
