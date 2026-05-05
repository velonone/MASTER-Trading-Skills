# Tutorial 4: LLM Agent Integration

Export MASTER Trading skills as tools for LLM agents.

## Basic Setup

```python
from skills.core import registry
from skills.agent import AgentToolAdapter
from skills.adversarial import FOMODetector
from skills.signals import OrderBookImbalance

# Register skills
registry.register(FOMODetector())
registry.register(OrderBookImbalance())

# Create adapter
adapter = AgentToolAdapter(registry)
```

## OpenAI Integration

```python
import openai

# Export tools
tools = adapter.export_openai_tools()

# Use in chat completion
response = openai.chat.completions.create(
    model="gpt-4-turbo",
    messages=[
        {"role": "system", "content": "You are a quantitative trading analyst."},
        {"role": "user", "content": "Is BTC showing FOMO right now?"},
    ],
    tools=tools,
    tool_choice="auto",
)

# Handle tool calls
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        result = await adapter.dispatch(
            tool_call.function.name,
            json.loads(tool_call.function.arguments),
        )
        print(result)
```

## Anthropic Integration

```python
import anthropic

client = anthropic.Anthropic()

# Export Anthropic-format tools
tools = adapter.export_anthropic_tools()

message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "Analyze BTC order book imbalance"}],
)
```

## Custom Skill Registration

```python
from skills.core.base import BaseSkill
from skills.core.types import Signal, SignalAction

class MyCustomSkill(BaseSkill):
    name = "custom_analyzer"
    description = "My custom market analysis tool"
    
    async def run(self, context: dict):
        symbol = context.get("symbol", "BTC/USDT")
        # Your analysis logic
        return {"symbol": symbol, "recommendation": "HOLD"}

registry.register(MyCustomSkill())
adapter = AgentToolAdapter(registry)  # Auto-picks up new skill
```

## Context Window Management

The adapter automatically truncates outputs exceeding ~4k tokens:

```python
# Large output gets truncated
result = await adapter.dispatch("some_skill", {"large_data": "x" * 20000})
# → {"result": "xxx... [truncated]"}
```

## Best Practices

1. Register only the skills relevant to the agent's domain
2. Use `registry.auto_discover("skills")` for automatic registration
3. Validate tool call arguments before dispatch
4. Handle errors gracefully — skills may fail due to missing API keys
