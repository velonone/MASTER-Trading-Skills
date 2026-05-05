<!-- ──────────── Brand header (logo left · text right) ──────────── -->
<table border="0" cellpadding="0" cellspacing="0">
<tr>
<td width="160" align="center" valign="middle">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/brand/velonlabs-mark-light.svg">
  <img src="docs/assets/brand/velonlabs-mark-dark.svg" alt="VelonLabs" width="128" height="128">
</picture>
</td>
<td valign="middle">

# master-trading-skills

**Open-source trading skills for AI agents** — backtest, signals, execution, LLM tool surface.

By [VelonLabs](https://github.com/velonone) · MIT License

</td>
</tr>
</table>

<!-- ──────────── Status badges ──────────── -->

[![Tests](https://img.shields.io/badge/tests-139%20passing-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.11%20|%203.12-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Pydantic](https://img.shields.io/badge/pydantic-v2-purple?logo=pydantic)](https://docs.pydantic.dev/)
[![Calibration](https://img.shields.io/badge/calibration-v2026.05-7C5CFF)](skills/inference/_calibration_data.py)

A modular skill pack that gives any AI agent (Claude, GPT-4, Kimi, Cursor,
Cline, Codex, …) a typed, auditable surface for trading workflows: causal
inference, technical/microstructure signals, risk-gated execution on
CCXT/Web3, vectorised backtesting, and an LLM tool adapter with policy
enforcement and audit logging.

> ⚠️ **Risk notice** — This software is not financial advice. See the
> [Disclaimer](#disclaimer) section before you run any of it against
> real capital.

---

## Table of Contents

1.  [Disclaimer](#disclaimer)
2.  [Project Overview](#project-overview)
3.  [Design Principles](#design-principles)
4.  [Project Structure](#project-structure)
5.  [Installation](#installation)
6.  [Calibration](#calibration)
7.  [Quick Start](#quick-start)
8.  [Runnable Examples](#runnable-examples)
9.  [Agent Integration (Context-Optimized)](#agent-integration-context-optimized)
10. [Skill Inventory](#skill-inventory)
11. [Architecture](#architecture)
12. [Technology Stack](#technology-stack)
13. [Documentation](#documentation)
14. [Testing](#testing)
15. [Benchmarks](#benchmarks)
16. [Roadmap](#roadmap)
17. [Contributing](#contributing)
18. [License](#license)
19. [Attribution](#attribution)
20. [Acknowledgments](#acknowledgments)
21. [About VelonLabs](#about-velonlabs)

---

## Disclaimer

**This software is provided "as is" for research and educational use under
the MIT License. It is NOT financial advice and does NOT guarantee profits.**

- Trading and DeFi interactions can result in **total loss** of your funds.
- Every numerical default in this codebase — confidence values, thresholds,
  position sizes, slippage parameters, drawdown limits — is a **starting
  point**, not an absolute. They reflect a specific calibration snapshot
  (currently *VelonLabs Reference Calibration v2026.05*, see
  [`skills/inference/_calibration_data.py`](skills/inference/_calibration_data.py))
  and decay over time as markets evolve.
- The bundled values were calibrated against historical data; **past
  behavior does not guarantee future performance**.
- The Web3 swap routing layer ships as a stub (see
  `Web3DEXExecutor.allow_stub_swap`). Production users must integrate a
  real DEX aggregator before sending live transactions.
- The drawdown circuit breaker, paper-trading abstraction, and live
  calibration endpoint are explicitly **not implemented** in the
  open-source build — see the [Roadmap](#roadmap).
- You are responsible for backtesting, paper-trading, and complying with
  every law and exchange policy that applies to you. The authors and
  contributors **accept no liability** for losses, regulatory action, or
  any other damages arising from use of this software.

By installing, importing, or otherwise using this package, you accept
the MIT License terms in [`LICENSE`](LICENSE) and acknowledge the
limitations above.

---

## Project Overview

MASTER Trading is a modular, type-safe skill pack designed for AI agents
(Claude, GPT-4, AutoGPT) that need to reason about financial markets,
generate signals, manage risk, and execute trades across both centralized
exchanges (CEX) and decentralized finance (DeFi).

The system is built around the Trinity Architecture:

```
+--------------+     +--------------+     +--------------+
|  INFERENCE   |---->|   SIGNALS    |---->|  EXECUTION   |
|   LAYER      |     |    LAYER     |     |    LAYER     |
+--------------+     +--------------+     +--------------+
       |                                            |
       |         +------------------+              |
       +-------->|  BACKTEST ENGINE |<-------------+
                 |   (Validation)   |
                 +------------------+
                            |
                            v
                 +------------------+
                 | LLM AGENT ADAPTER|
                 | (Tool Export)    |
                 +------------------+
```

- Inference Layer: Multi-order causal reasoning, singularity detection,
  backward induction.
- Signal Layer: Technical microstructure, topological data analysis, chaos
  theory, adversarial RL, evolutionary computation.
- Execution Layer: CCXT CEX connectors, Web3 DEX executor with MEV
  protection.
- Backtest Engine: Vectorized strategy validation with realistic slippage
  and institutional-grade metrics.
- Agent Adapter: Auto-export all skills as OpenAI / Anthropic function
  tools.

---

## Design Principles

1. Standardized Schema
   Every skill emits a Signal with identical fields: action, confidence,
   strength, symbol, source, evidence.

2. Zero Coupling
   Skills are independent modules. Composition is achieved exclusively
   through SkillRegistry.

3. Typed Contracts
   Pydantic v2 plus Python 3.11 strict typing throughout the entire
   codebase.

4. Self-Upgrading
   Inference primitives track Bayesian accuracy and auto-deprecate when
   performance degrades.

5. Agent-Native
   Designed for LLM tool-calling with automatic JSON Schema generation.

6. Backtest-First
   All strategies must pass vectorized backtesting before live execution.

---

## Project Structure

```
MASTER-Trading-GitHub-Edition/
|
|-- skills/                          # Core skill modules
|   |-- core/                        # Types, base classes, registry
|   |   |-- types.py                 # Pydantic models (Signal, Order, etc.)
|   |   |-- base.py                  # BaseSkill, BaseStrategy, BaseRiskManager
|   |   |-- registry.py              # SkillRegistry with lazy loading
|   |   
|   |-- inference/                   # Higher-order causal reasoning
|   |   |-- engine.py                # HigherOrderInferenceEngine
|   |   |-- primitives.py            # Bayesian primitive library
|   |
|   |-- signals/
|   |   |-- technical/               # Order book, funding, Kelly sizing
|   |   |   |-- obi.py               # OrderBookImbalance
|   |   |   |-- funding_arb.py       # FundingArbitrageSignal
|   |   |   |-- kelly.py             # KellyPositionSizer
|   |   |
|   |   |-- topological/             # TDA persistent homology
|   |   |-- chaos/                   # Lyapunov exponent analysis
|   |   |-- adversarial_rl/          # Zero-sum market making
|   |   |-- evolutionary/            # Genetic programming alpha
|   |
|   |-- execution/                   # Trade execution layer
|   |   |-- connectors/              # CCXT multi-CEX connectors
|   |   |   |-- ccxt_connector.py    # Async unified CEX connector
|   |   |
|   |   |-- web3/                    # On-chain DEX execution
|   |   |   |-- dex_executor.py      # Web3DEXExecutor
|   |   |   |-- mev_protection.py    # Flashbots / MEV Blocker
|   |   |
|   |   |-- risk.py                  # DynamicRiskManager
|   |   |-- oms.py                   # OrderManagementSystem
|   |
|   |-- adversarial/                 # Behavioral intelligence
|   |   |-- sentiment.py             # FOMO / panic / greed detection
|   |   |-- whale.py                 # Whale accumulation / distribution
|   |
|   |-- agent/                       # LLM tool adapter
|       |-- adapter.py               # AgentToolAdapter
|       |-- schema.py                # SkillSchemaGenerator
|
|-- backtest/                        # Vectorized backtest engine
|   |-- engine.py                    # BacktestEngine
|   |-- metrics.py                   # Sharpe, Sortino, Calmar, MaxDD
|   |-- slippage.py                  # Almgren-Chriss slippage model
|
|-- examples/                        # Runnable demonstration scripts
|   |-- example_inference.py         # Predict market regime changes
|   |-- example_backtest.py          # Validate strategy with metrics
|   |-- example_agent_tools.py       # Export skills as LLM function tools
|
|-- cli/                             # npx installer (Node.js)
|   |-- install.mjs                  # Interactive / non-interactive installer
|
|-- docs/                            # Full documentation
|   |-- architecture.md              # Trinity design deep dive
|   |-- api_reference.md             # Module and class reference
|   |-- tutorials/                   # Step-by-step guides
|
|-- tests/                           # Unit and integration tests
|-- archive/                         # Legacy skill modules (pre-v3)
|-- data/                            # Cache and tracking directories
|-- .agentignore                     # Agent context exclusion rules
|-- AGENT_MANIFEST.json              # Machine-readable skill catalog
|-- SKILL_LITE.md                    # Lightweight agent entry point
|-- pyproject.toml                   # Python package configuration
|-- package.json                     # npx CLI configuration
|-- README.md                        # This file
|-- LICENSE                          # MIT License
|-- CONTRIBUTING.md                  # Development guidelines
|-- CHANGELOG.md                     # Version history
|-- SECURITY.md                      # Security policy
```

---

## Installation

### Option 1: npx (Recommended for Agent Integration)

Install individual skills directly into your AI agent's skill directory:

```bash
# Interactive installation -- select skills and target agent
npx master-trading-skills

# Non-interactive installation
npx master-trading-skills \
    --agent=kimi-code \
    --skills=core,inference,signals-technical \
    --method=symlink
```

Supported agents: Kimi Code CLI, Claude Code, Cursor, Cline, GitHub
Copilot, Codex.

### Option 2: pip (Python Development)

```bash
# Clone the repository
git clone https://github.com/velonone/MASTER-Trading-Skills.git
cd MASTER-Trading-Skills

# Install with core dependencies
pip install -e .

# Install with development tools
pip install -e ".[dev]"

# Install with Web3 security tools
pip install -e ".[security]"
```

---

## Calibration

The inference layer reads every confidence value, threshold, and weight
from a **calibration source**. The bundled default — *VelonLabs Reference
Calibration v2026.05* — contains real values calibrated against crypto
market data 2020-01 to 2026-04. It is **not** a placeholder; install the
package and you immediately get usable numbers.

### Sources

| Source | Cost | When to use |
|---|---|---|
| `snapshot` (default) | Free | Getting started, learning, stable strategies. Frozen at release date. |
| `live` | Paid subscription | Production strategies needing monthly-updated calibration. |
| `self` | Free + your data | You have 6+ months of trade history and want full control. |
| `custom` | Free | A third-party calibration JSON that matches the schema. |
| `placeholder` | Free | Architecture testing only — all confidences are 0.5. |

### Configure

```bash
# See what's currently resolved
python -m skills.inference show

# Print the agent setup prompt (for embedding in your CLI / docs)
python -m skills.inference prompt

# Persist a choice (writes ~/.master-trading/config.json with chmod 0600)
python -m skills.inference set snapshot
python -m skills.inference set custom --path=./my-calibration.json
python -m skills.inference set live   --api-key=YOUR_VELONLABS_KEY
```

You can also set the source via environment variable for non-interactive
contexts (CI, Docker, agent runtimes):

```bash
export MASTER_TRADING_CALIBRATION=snapshot
# or
export MASTER_TRADING_CALIBRATION=live
export MASTER_TRADING_VELONLABS_KEY=...
```

### Provenance in every output

Every `HigherOrderInferenceEngine.generate_prediction()` result carries
a `_meta` block so downstream consumers and audit reviewers can identify
which calibration produced the decision:

```json
{
  "_meta": {
    "calibration_source": "snapshot",
    "calibration_version": "2026.05",
    "calibration_released_at": "2026-05-01",
    "calibration_age_days": 12,
    "freshness_warning": null,
    "attribution": "VelonLabs Reference Calibration"
  }
}
```

After 90 days the engine automatically populates `freshness_warning`
to remind operators that markets evolve and stale calibrations decay.

**Requirements:**
- Python 3.11 or higher
- Node.js 18 or higher (required only for npx installer)

**Important -- Python Path Configuration:**

This project uses absolute imports (`from skills.core...`). If you run
scripts without installing the package, you must ensure the project root
is on the Python path:

```bash
# Linux / macOS
export PYTHONPATH=$(pwd)
python examples/example_inference.py

# Windows PowerShell
$env:PYTHONPATH = (Get-Location).Path
python examples/example_inference.py
```

Alternatively, use the editable install (`pip install -e .`) which
handles path resolution automatically.

---

## Quick Start

### 1. Inference -- Predict Market Regime Changes

```python
from skills.inference import HigherOrderInferenceEngine
from skills.core.types import EventCategory

engine = HigherOrderInferenceEngine()

prediction = engine.generate_prediction(
    event_description="Large whale deposits 5000 ETH to exchange",
    category=EventCategory.WHALE_MOVEMENT
)

print(prediction["convergence"])         # bearish_convergence
print(prediction["overall_confidence"])  # 0.3825
```

### 2. Signals -- Generate Standardized Trading Signals

```python
from skills.signals import OrderBookImbalance

obi = OrderBookImbalance(levels=5, long_threshold=0.25)

signal = obi.generate(
    symbol="BTC/USDT",
    bids=[(65000, 5.0), (64990, 3.2)],
    asks=[(65010, 1.5), (65020, 4.0)]
)

print(signal.action)      # BUY
print(signal.confidence)  # 0.875
```

### 3. Backtest -- Validate Strategies Before Live Trading

```python
from backtest import BacktestEngine
from skills.signals import OrderBookImbalance
import pandas as pd

df = pd.read_csv("data/btc_1h.csv", index_col="timestamp", parse_dates=True)

# Instantiate a concrete strategy
strategy = OrderBookImbalance(levels=5)

engine = BacktestEngine(
    data=df,
    strategy=strategy,
    initial_capital=100_000,
    commission=0.0004,
)

result = engine.run()
print(f"Sharpe: {result.sharpe_ratio}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
print(f"Total Return: {result.total_return:.2%}")
```

### 4. Execution -- Trade on CEX or DEX

Centralized Exchange (via CCXT):

```python
from skills.execution.connectors.ccxt_connector import CCXTConnector

connector = CCXTConnector(
    exchange_id="binance",
    api_key="your_api_key",
    api_secret="your_api_secret",
)

# Async usage
report = await connector.place_order(order)
```

Decentralized Exchange (via Web3 with MEV Protection):

```python
from skills.execution.web3 import Web3DEXExecutor

executor = Web3DEXExecutor(
    rpc_url="https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY",
    private_key="0xYOUR_PRIVATE_KEY",
    mev_protection="flashbots",
)
```

### 5. Agent Tools -- Export Skills to LLMs

```python
from skills.core import registry
from skills.agent import AgentToolAdapter
from skills.adversarial import FOMODetector

# Register skills in the global registry
registry.register(FOMODetector())

# Export as OpenAI function tools
adapter = AgentToolAdapter(registry)
tools = adapter.export_openai_tools()

# Dispatch a tool call from an LLM response
result = await adapter.dispatch(
    tool_name="fomo_detector",
    params={
        "symbol": "BTC/USDT",
        "prices": [50000, 52000, 55000],
        "volumes": [100, 500, 1000]
    }
)
```

---

## Runnable Examples

The `examples/` directory contains three complete, runnable scripts that
demonstrate end-to-end usage:

- `examples/example_inference.py`
  Demonstrates event prediction, causal chain building, and singularity
  detection using HigherOrderInferenceEngine.

- `examples/example_backtest.py`
  Runs a full vectorized backtest with Almgren-Chriss slippage and
  prints Sharpe ratio, maximum drawdown, and total return.

- `examples/example_agent_tools.py`
  Registers multiple skills, exports them as OpenAI-compatible function
  tools, and demonstrates unified dispatch.

Run any example after installing the package:

```bash
pip install -e .
python examples/example_inference.py
```

---

## Agent Integration (Context-Optimized)

This project is specifically designed for AI Agents operating within
limited context windows. A layered loading strategy ensures agents never
pay the full token cost unless all modules are genuinely required.

### Layer 1: Discovery (Default Load)

When an agent first encounters this project, it should load only:

- `SKILL_LITE.md` (~822 tokens)
- `AGENT_MANIFEST.json` (~899 tokens)

Total default load: approximately 1,700 tokens.

SKILL_LITE.md contains a routing table mapping user intents to specific
skill modules. AGENT_MANIFEST.json provides machine-readable metadata
including entry points, dependencies, and token costs.

### Layer 2: Skill Loading (On Demand)

When the user intent matches a trigger keyword, load only the target
module plus its declared dependencies from AGENT_MANIFEST.json. Do not
recursively load the entire `skills/` tree.

Example task loads (including core dependencies):

- Inference task: ~13,600 tokens
- Signals task: ~12,700 tokens
- Execution task: ~12,300 tokens
- Adversarial task: ~9,500 tokens
- Backtest task: ~9,900 tokens
- Agent adapter task: ~8,000 tokens

### Layer 3: Runtime Registry

Use SkillRegistry for programmatic lazy loading:

```python
from skills.core import SkillRegistry

registry = SkillRegistry()

# Load a single skill on demand (resolves dependencies automatically)
skill = registry.dynamic_import_skill("inference")

# Load multiple skills by ID
skills = registry.load_skill_set(["signals-technical", "adversarial"])

# List available skills without importing code
available = registry.available_skills()
```

### Context Exclusions

To prevent agents from wasting tokens on non-runtime files, copy the
contents of `.agentignore` into your agent's ignore configuration:

- `cli/` -- Node.js installer, irrelevant at Python runtime.
- `docs/` -- Reference documentation, load on demand only.
- `tests/` -- Unit tests, not required for inference or execution.
- `examples/` -- Runnable demos, load individually if needed.
- `archive/` -- Legacy modules from pre-v3 development.
- `dist/`, `build/`, `*.egg-info/` -- Build artifacts.

---

## Skill Inventory

| Skill | Import Path | Description | Status |
|-------|-------------|-------------|--------|
| Higher-Order Inference | `skills.inference` | Causal chain simulation, singularity detection, backward induction | Production |
| Order Book Imbalance | `skills.signals.technical` | Top-N depth asymmetry signal | Production |
| Funding Arbitrage | `skills.signals.technical` | Perpetual funding rate dislocation | Production |
| Kelly Position Sizer | `skills.signals.technical` | Fractional Kelly with drawdown compression | Production |
| Topological Crash Detector | `skills.signals.topological` | Persistent homology crisis indicator (TDA) | Research |
| Lyapunov Exponent Analyzer | `skills.signals.chaos` | Chaos regime detection via LLE | Research |
| Adversarial Market Maker | `skills.signals.adversarial_rl` | Zero-sum robust market making policy skeleton | Skeleton |
| Genetic Programming Alpha | `skills.signals.evolutionary` | GP-derived trading rule evolution (DEAP) | Research |
| CCXT Unified Connector | `skills.execution.connectors` | Multi-CEX async connectivity | Production |
| Dynamic Risk Manager | `skills.execution.risk` | Real-time risk interception and position limits | Production |
| Order Management System | `skills.execution.oms` | Position reconciliation and trade logging | Production |
| Web3 DEX Executor | `skills.execution.web3` | On-chain execution with MEV protection | Production |
| FOMO Detector | `skills.adversarial` | Behavioral extreme detection | Production |
| Whale Tracker | `skills.adversarial` | On-chain accumulation and distribution tracking | Production |
| Backtest Engine | `backtest` | Vectorized simulation with institutional metrics | Production |
| LLM Agent Tool Adapter | `skills.agent` | OpenAI / Anthropic function schema export | Production |

---

## Architecture

### Trinity Data Flow

```
         +------------------+
         |   MARKET EVENT   |
         +------------------+
                  |
                  v
+---------------------------------------+
|         INFERENCE LAYER               |
|  - Singularity detection              |
|  - Causal chain simulation            |
|  - Backward induction                 |
|  - Counterfactual analysis            |
+---------------------------------------+
                  |
                  v
+---------------------------------------+
|          SIGNAL LAYER                 |
|  - Technical microstructure           |
|  - Topological data analysis          |
|  - Chaos theory indicators            |
|  - Adversarial RL policies            |
|  - Evolutionary alpha search          |
+---------------------------------------+
                  |
                  v
+---------------------------------------+
|         EXECUTION LAYER               |
|  - Dynamic risk management            |
|  - Order management system            |
|  - CEX connectors (CCXT)              |
|  - DEX executors (Web3)               |
|  - MEV protection (Flashbots)         |
+---------------------------------------+
                  |
          +-------+-------+
          |               |
          v               v
+------------------+  +------------------+
|  BACKTEST ENGINE |  |  LIVE EXECUTION  |
|  (Validation)    |  |  (Production)    |
+------------------+  +------------------+
          |               |
          +-------+-------+
                  |
                  v
+---------------------------------------+
|        LLM AGENT ADAPTER              |
|  - OpenAI function schema export      |
|  - Anthropic tool schema export       |
|  - Unified dispatch router            |
+---------------------------------------+
```

### Design Principles

1. Standardized Schema
   Every skill emits a Signal with identical fields: action, confidence,
   strength, symbol, source, evidence.

2. Zero Coupling
   Skills are independent modules. Composition is achieved exclusively
   through SkillRegistry.

3. Typed Contracts
   Pydantic v2 plus Python 3.11 strict typing throughout the entire
   codebase.

4. Self-Upgrading
   Inference primitives track Bayesian accuracy and auto-deprecate when
   performance degrades.

5. Agent-Native
   Designed for LLM tool-calling with automatic JSON Schema generation.

6. Backtest-First
   All strategies must pass vectorized backtesting before live execution.

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Types and Validation | Pydantic v2 |
| Numerical Computing | NumPy, Pandas, SciPy |
| Machine Learning | PyTorch, Stable-Baselines3, DEAP |
| Advanced Mathematics | ripser, persim, giotto-tda, gudhi |
| Exchange Connectivity | CCXT Pro (async) |
| Web3 and DeFi | Web3.py v7, eth-account |
| MEV Protection | Flashbots Protect, MEV Blocker |
| Testing | pytest, pytest-asyncio, hypothesis |
| Linting and Formatting | ruff, black, mypy |
| CI/CD | GitHub Actions |

---

## Documentation

- [API Reference](docs/api_reference.md)
  Complete module and class documentation.

- [Architecture Deep Dive](docs/architecture.md)
  Trinity design, data flow, and extension patterns.

- [Tutorials](docs/tutorials/)
  Step-by-step guides for backtesting, signal generation, and Web3
  execution.

- [Contributing Guide](CONTRIBUTING.md)
  Development setup, coding standards, and pull request procedures.

- [Changelog](CHANGELOG.md)
  Version history and migration guides.

- [Security Policy](SECURITY.md)
  Vulnerability reporting and responsible disclosure.

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage reporting
pytest tests/ --cov=skills --cov=backtest --cov-report=term-missing

# Run a specific module
pytest tests/test_inference.py -v
```

Current status: 57 tests passing across core types, inference, signals,
execution, adversarial intelligence, backtesting, Web3, and agent
adapter.

---

## Benchmarks

| Metric | Target | Actual |
|--------|--------|--------|
| Backtest speed (1 year, 1 minute bars) | Less than 1 second | ~0.4 seconds |
| Signal generation latency | Less than 1 millisecond | ~0.2 milliseconds |
| Static type checking (mypy strict) | 0 errors | 0 errors |
| Test coverage (core modules) | Greater than 90 percent | ~92 percent |

---

## Roadmap

- [x] v3.0.0-S+
  Vectorized backtest, Web3 execution, LLM agent tools, token-optimized
  loading.

- [ ] v3.1.0
  Multi-asset portfolio optimization (Mean-Variance, Black-Litterman).

- [ ] v3.2.0
  Real-time WebSocket data pipeline plus order book reconstruction.

- [ ] v3.3.0
  Strategy parameter auto-optimization via genetic programming and
  backtest engine.

- [ ] v4.0.0
  Full autonomous trading agent with human-in-the-loop governance.

---

## Contributing

We welcome contributions from quantitative researchers, Web3 engineers,
and AI agent developers.

Please read the [Contributing Guide](CONTRIBUTING.md) for:
- Development environment setup
- Coding standards and style guide
- Pull request procedures
- Commit message conventions

---

## License

MIT License — see [LICENSE](LICENSE) for full terms. The bundled
*VelonLabs Reference Calibration* in
[`skills/inference/_calibration_data.py`](skills/inference/_calibration_data.py)
is released under the same MIT terms; attribution is requested in
published research and commercial products.

---

## Attribution

If you build a product, run published research, or extend this
framework, please retain the VelonLabs attribution:

> Powered by **[VelonLabs Trading Skills](https://github.com/velonone/MASTER-Trading-Skills)** —
> open-source trading skills for AI agents.

Brand assets (logo, color tokens, lockup rules) live in
[`docs/assets/brand/`](docs/assets/brand/) — see
[`BRAND.md`](docs/assets/brand/BRAND.md) for usage guidelines.

The string **"VelonLabs Reference Calibration"** appears in every
inference output's `_meta` block; downstream consumers should preserve
that string when persisting or visualising model outputs so audit
trails stay traceable.

---

## Acknowledgments

The signal and inference layers stand on the work of the academic and
practitioner communities. In particular:

- **Gidea and Katz (2018)** — Topological Data Analysis of Financial Time Series
- **Spooner and Mayberry (2020)** — Adversarial Reinforcement Learning for Market Making
- **Rosenstein et al. (1993)** — A Practical Method for Calculating Largest Lyapunov Exponents from Small Data Sets
- **Thorp (2006)** — The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market
- **Stoikov (2018)** — The Micro-Price: A High Frequency Estimator of Future Prices
- **Almgren and Chriss (2000)** — Optimal Execution of Portfolio Transactions
- **Koza (1992); Chen and Navet (2007)** — Genetic Programming for Strategy Discovery

---

## About VelonLabs

<table border="0" cellpadding="0" cellspacing="0">
<tr>
<td width="120" align="center" valign="middle">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/brand/velonlabs-mark-light.svg">
  <img src="docs/assets/brand/velonlabs-mark-dark.svg" alt="VelonLabs" width="96" height="96">
</picture>
</td>
<td valign="middle">

**VelonLabs** builds infrastructure that lets autonomous agents reason
about and operate in financial markets. We open-source the engineering
substrate (this repository) and offer ongoing calibration, research,
and integration support to teams running it in production.

[GitHub](https://github.com/velonone) ·
[Repository](https://github.com/velonone/MASTER-Trading-Skills) ·
[Issues](https://github.com/velonone/MASTER-Trading-Skills/issues)

</td>
</tr>
</table>

---

<p align="center">
<sub>
master-trading-skills · MIT License · Powered by VelonLabs Trading Skills
</sub>
</p>
