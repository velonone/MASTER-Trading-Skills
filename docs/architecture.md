# Architecture

## Trinity Design Philosophy

MASTER Trading is built around three cognitive layers that mirror how institutional quant firms operate:

1. **Inference** — *What will happen?*  
   Multi-order causal reasoning, singularity detection, and counterfactual analysis.

2. **Signals** — *What should we do?*  
   Mathematical and ML-based alpha generation across multiple paradigms.

3. **Execution** — *How do we do it?*  
   Risk-managed order routing to CEX and DEX venues with MEV protection.

## Data Flow

```
Market Event (price, on-chain, news)
    │
    ▼
┌─────────────────────────────────────┐
│  Inference Layer                    │
│  - Singularity detection            │
│  - Causal chain simulation          │
│  - Primitive matching               │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Signal Layer                       │
│  - Technical microstructure         │
│  - Topological / chaos analysis     │
│  - Adversarial / evolutionary ML    │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Backtest Engine (S+)               │
│  - Vectorized simulation            │
│  - Slippage + commission modeling   │
│  - Sharpe / Sortino / Calmar        │
└─────────────────────────────────────┘
    │ (validated strategies only)
    ▼
┌─────────────────────────────────────┐
│  Risk Manager                       │
│  - Position limits                  │
│  - Drawdown circuit breakers        │
│  - Velocity controls                │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Execution Layer                    │
│  - CCXT CEX connector               │
│  - Web3 DEX + MEV protection        │
│  - Order Management System          │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Feedback Loop                      │
│  - Fill → PnL tracking              │
│  - Primitive accuracy update        │
│  - LLM agent tool dispatch          │
└─────────────────────────────────────┘
```

## Module Boundaries

### Core (`skills/core/`)
The only module that all other modules depend on. Contains universal types and abstract base classes. Changes here require careful review as they affect every skill.

### Inference (`skills/inference/`)
Pure logic, no external data dependencies. Operates on symbolic event descriptions and outputs causal chains.

### Signals (`skills/signals/`)
Each sub-module is independent. They consume `MarketData` and emit `Signal` objects. No cross-dependencies between signal modules.

### Execution (`skills/execution/`)
Venue-specific code isolated in connector modules. The OMS and risk manager are venue-agnostic.

### Adversarial (`skills/adversarial/`)
Behavioral modeling and opponent analysis. Consumes on-chain and market data.

### Backtest (`backtest/`)
Validates signals before live deployment. Depends on core types but not on execution connectors.

### Agent (`skills/agent/`)
Thin adapter layer. Depends on core registry but not on specific skill implementations.

## Type System

All inter-module communication uses Pydantic v2 models defined in `skills/core/types.py`:

- `Signal` — universal output of every strategy
- `Order` — standardized order request
- `Position` — normalized position state
- `Trade` / `ExecutionReport` — fill telemetry
- `MarketData` — normalized OHLCV + order book snapshot
- `RiskLimit` — dynamic risk envelope

## Async Model

- **I/O-bound** operations (connectors, external APIs) are `async`
- **CPU-bound** operations (backtest simulation, signal generation) are synchronous
- The OMS uses `asyncio.Lock` for thread-safe state updates
