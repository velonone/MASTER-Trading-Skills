---
name: master-trading
version: 3.0.0-splus
description: |
  S+ Grade Universal Trading Skill Pack for AI Agents.
  Trinity Architecture: Inference → Signal → Execution → Self-Upgrade.
  S+ Additions: Vectorized Backtest Engine, Web3 DEX Executor,
  LLM Agent Tool Adapter, CI/CD, 57 tests, >90% core coverage.
triggers:
  - trading strategy development
  - quantitative analysis
  - risk management
  - market making
  - DeFi protocol interaction
  - on-chain analytics
  - adversarial opponent modeling
  - MEV optimization
  - portfolio optimization
  - algorithmic execution
  - backtesting
  - LLM tool calling
---

# MASTER Trading Skill Pack v3.0.0-S+

> **From Theory to Live Execution** — A production-grade, agent-native trading cognitive system.  
> **S+ Certified**: Vectorized backtesting, Web3 execution, multi-provider LLM tools, 57 tests.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT RUNTIME                            │
│              (Claude / GPT-4 / AutoGPT / Local LLM)             │
└──────────────────────────┬──────────────────────────────────────┘
                           │ dispatches via SkillRegistry
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CORE ABSTRACTION                           │
│  Signal | Position | Order | Trade | MarketData | RiskLimit     │
│  BaseStrategy | BaseRiskManager | BaseConnector | BaseSkill     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  INFERENCE   │  │   SIGNALS    │  │  EXECUTION   │
│   LAYER      │  │    LAYER     │  │    LAYER     │
├──────────────┤  ├──────────────┤  ├──────────────┤
│• Singularity │  │• Technical   │  │• CCXT CEX    │
│  Detection   │  │  Microstruc- │  │  Connector   │
│• Causal Chain│  │  ture        │  │• Web3 DEX    │
│  Simulation  │  │• Topological │  │  Executor    │
│• Backward    │  │  Data Analysis│ │• Order Mgmt  │
│  Induction   │  │• Chaos Theory│  │  System      │
│• Counterfact-│  │• Adversarial │  │• Dynamic Risk│
│  ual Analysis│  │  RL          │  │  Manager     │
│• Primitive   │  │• Evolutionary│  │• MEV Protect │
│  Self-Upgrade│  │  Computation │  └──────────────┘
└──────────────┘  └──────────────┘
        │                  │
        └──────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ADVERSARIAL INTELLIGENCE                       │
│  FOMO Detection | Whale Tracking | Project Intent Analysis      │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKTEST ENGINE (S+)                         │
│  Vectorized Simulation | Slippage Model | Sharpe/Sortino/Calmar │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                 LLM AGENT TOOL ADAPTER (S+)                     │
│  OpenAI Functions | Anthropic Tool Use | Auto-Schema Generation │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Loading Guide

> **Context Window Optimization**: This pack includes a lite entry (`SKILL_LITE.md`, ~800 tokens) for agents with limited context. The full `README.md` and `docs/` are reference-only and should not be loaded at runtime.
>
> **Recommended load order**:
> 1. `SKILL_LITE.md` — Routing and quick reference
> 2. `skills/core/` — Universal types and registry
> 3. Other `skills/*` modules — On-demand based on user intent
>
> **Skip at runtime** (see `.agentignore`): `cli/`, `docs/`, `examples/`, `scripts/`, `tests/`, `archive/`

## Required Setup (Agent Behavior)

**Before producing any inference output for the user, the agent SHOULD
ensure the user has chosen a calibration source.** All causal-chain
confidences, singularity weights, and signal thresholds are read from
the active calibration — these numbers directly shape trading
recommendations, so the user must know which set is in use.

### Default behavior (non-strict)

`Calibration.resolve()` falls back to the bundled
**VelonLabs Reference Snapshot v2026.05** (real values, free).
The first inference output's `_meta` block will contain:

```json
{
  "calibration_source": "snapshot",
  "calibration_version": "2026.05",
  "fallback": true,
  "hint": "No calibration configured — using bundled snapshot. ..."
}
```

When the agent sees `fallback: true`, it **should**:

1. Surface the calibration choice prompt to the user **once per session**.
2. Use the `calibration_setup` skill to record the user's answer.

Retrieve the prompt via:
```python
result = await adapter.dispatch("calibration_setup", {"action": "prompt"})
# → {"status": "ok", "prompt": "<full multi-line prompt>"}
```

### Persisting the user's choice

```python
await adapter.dispatch("calibration_setup", {
    "source": "snapshot"            # or "live"/"self"/"custom"/"placeholder"
    # "path": "/abs/path.json"      # for "custom" or "self"
    # "api_key": "xxx"              # for "live"
})
# → writes ~/.master-trading/config.json (chmod 0600)
```

### Strict mode (production)

Operators who want setup to be a deliberate step rather than a silent
fallback can construct the engine in strict mode:

```python
engine = HigherOrderInferenceEngine(strict_calibration=True)
# raises CalibrationNotConfigured until env var or config file is set
```

The exception's `prompt` attribute is the same text the agent should
surface to the user.

### Auditing

Every inference output carries `_meta.calibration_source` and
`_meta.calibration_version`. After 90 days, snapshots automatically
emit `_meta.freshness_warning` so audit reviewers can spot stale
calibration without inspecting code.

---

## Quick Start

### 1. Install

**Via npx (into your agent's skill directory):**

The package is currently distributed via GitHub (not yet on the npm
registry). Install directly:

```bash
npx github:velonone/MASTER-Trading-Skills
```

Once published to npm, `npx master-trading-skills` will also work.

**Via pip (for Python development):**
```bash
pip install -e ".[dev]"
```

### 2. Register & Dispatch

```python
from skills.core import registry
from skills.core.types import EventCategory
from skills.inference import HigherOrderInferenceEngine
from skills.signals import OrderBookImbalance, FundingArbitrageSignal
from skills.adversarial import FOMODetector

# Auto-discover all skills
registry.auto_discover("skills")
print(registry.list_skills())

# Manual instantiation
engine = HigherOrderInferenceEngine()
prediction = engine.generate_prediction(
    "Whale deposits 5000 ETH to exchange",
    EventCategory.WHALE_MOVEMENT
)
```

### 3. Backtest Strategy (S+)

```python
from backtest import BacktestEngine
import pandas as pd

df = pd.read_csv("btc_1h.csv", index_col="timestamp", parse_dates=True)
engine = BacktestEngine(
    data=df,
    strategy=my_signal_strategy,
    initial_capital=100_000,
    commission=0.0004,
)
result = engine.run()
print(f"Sharpe: {result.sharpe_ratio}, MaxDD: {result.max_drawdown}")
```

### 4. LLM Tool Calling (S+)

```python
from skills.agent import AgentToolAdapter
from skills.core import registry

# Register skills
registry.register(FOMODetector())

# Export to OpenAI/Anthropic
adapter = AgentToolAdapter(registry)
tools = adapter.export_openai_tools()
# → [{"type": "function", "function": {"name": "fomo_detector", ...}}]

# Dispatch from LLM response
result = await adapter.dispatch("fomo_detector", {"symbol": "BTC/USDT", "prices": [...]})
```

### 5. Web3 Execution (S+)

```python
from skills.execution.web3 import Web3DEXExecutor

executor = Web3DEXExecutor(
    rpc_url="https://eth-mainnet.g.alchemy.com/v2/...",
    private_key="0x...",
    mev_protection="flashbots",
)
tx = await executor.swap_exact_in(
    token_in="0xA0b86a33E6441e6C7D3D4B4f6c7E8F9a0B1c2D3e",
    token_out="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    amount_in=Decimal("1.5"),
    min_amount_out=Decimal("1.4"),
)
receipt = await executor.await_confirmation(tx, confirmations=2)
```

## Skill Inventory

| Skill | Module | Type | Status |
|-------|--------|------|--------|
| Higher-Order Inference | `skills.inference` | Inference | ✅ Production |
| Order Book Imbalance | `skills.signals.technical` | Signal | ✅ Production |
| Funding Arbitrage | `skills.signals.technical` | Signal | ✅ Production |
| Kelly Position Sizer | `skills.signals.technical` | Risk | ✅ Production |
| Topological Crash Detector | `skills.signals.topological` | Signal | ✅ Research |
| Lyapunov Exponent Analyzer | `skills.signals.chaos` | Signal | ✅ Research |
| Adversarial Market Maker | `skills.signals.adversarial_rl` | Execution | ✅ Skeleton |
| Genetic Programming Alpha | `skills.signals.evolutionary` | Signal | ✅ Research |
| CCXT Unified Connector | `skills.execution.connectors` | Execution | ✅ Production |
| Dynamic Risk Manager | `skills.execution.risk` | Risk | ✅ Production |
| Order Management System | `skills.execution.oms` | Execution | ✅ Production |
| **Web3 DEX Executor** | `skills.execution.web3` | Execution | ✅ **S+** |
| **MEV Protection** | `skills.execution.web3` | Execution | ✅ **S+** |
| FOMO Detector | `skills.adversarial` | Sentiment | ✅ Production |
| Whale Tracker | `skills.adversarial` | On-Chain | ✅ Production |
| **Backtest Engine** | `backtest` | Validation | ✅ **S+** |
| **LLM Agent Tool Adapter** | `skills.agent` | Agent Interface | ✅ **S+** |

## Trinity Decision Flow

```
Market Event
    │
    ▼
Singularity Detection ──No──► Ignore (noise)
    │ Yes
    ▼
Build Causal Chain (Inference)
    │
    ▼
Validate with Theory (TDA / Chaos / Physics)
    │
    ▼
Generate Signal ( standardized schema )
    │
    ▼
Risk Interception (Dynamic Risk Manager)
    │
    ▼
Backtest Validation (Vectorized Engine) ──Fail──► Refine Strategy
    │ Pass
    ▼
Execute via Connector (CCXT / Web3 + MEV Protection)
    │
    ▼
Observe Outcome ──► Update Primitive Accuracy (Self-Upgrade)
    │
    ▼
LLM Agent Feedback Loop (Tool Adapter)
```

## S+ Upgrade Highlights

### A. Vectorized Backtest Engine
- **Performance**: Bar-by-bar simulation with NumPy/Pandas; 1 year of 1h data in <1s
- **Realism**: Volatility-adjusted slippage (Almgren-Chriss), limit order fill simulation, commission modeling
- **Metrics**: Sharpe, Sortino, Calmar, Max Drawdown, Profit Factor, Win Rate

### B. Web3 DEX Executor
- **MEV Protection**: Flashbots Protect (default), MEV Blocker, Eden Network
- **Gas Optimization**: EIP-1559 dynamic fee estimation
- **Transaction Lifecycle**: Async signing, broadcast, confirmation with re-org safety

### C. LLM Agent Tool Adapter
- **Auto-Schema**: Every `BaseSkill` auto-exports JSON Schema via Pydantic
- **Multi-Provider**: OpenAI Functions + Anthropic Tool Use from same definitions
- **Context Guard**: Automatic truncation for outputs >4k tokens

### D. DevOps
- **CI/CD**: GitHub Actions with Python 3.11/3.12 matrix
- **Code Quality**: ruff lint, black format, mypy strict type checking
- **Tests**: 57 unit tests, asyncio-compatible, >90% core coverage

## Design Principles

1. **Standardized Schema**: Every skill emits `Signal` with identical fields.
2. **Zero Coupling**: Skills are independent; compose via Agent runtime.
3. **Typed Contracts**: Pydantic v2 + Python 3.11+ strict typing.
4. **Self-Upgrading**: Inference primitives track accuracy and auto-deprecate.
5. **Agent-Native**: Designed for LLM tool-calling (Function Calling compatible).
6. **S+ Hardening**: Backtest validation before live execution; MEV protection by default.

## API Compatibility

All public methods are async where I/O occurs (connectors, external APIs).  
Signal generation is synchronous for low-latency paths.  
Backtest engine is vectorized for batch simulation.

## References

- Gidea & Katz (2018): TDA of Financial Time Series
- Spooner & Mayberry (2020): Adversarial RL for Market Making
- Rosenstein et al. (1993): Practical LLE Calculation
- Thorp (2006): The Kelly Criterion
- Stoikov (2018): The Micro-Price
- Almgren & Chriss (2000): Optimal Execution of Portfolio Transactions

## License

MIT — VelonLabs
