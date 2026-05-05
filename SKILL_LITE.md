---
name: master-trading
version: 3.0.0-splus-lite
description: |
  Lightweight entry point for AI Agents with limited context windows.
  Loads only essential metadata and routing info.
  For full documentation, see README.md and docs/.
triggers:
  - trading strategy
  - quantitative analysis
  - risk management
  - market making
  - DeFi execution
  - on-chain analytics
  - adversarial modeling
  - MEV optimization
  - portfolio optimization
  - backtesting
  - LLM tool calling
---

# MASTER Trading Skill Pack — Lite Entry

> **Optimized for Agent context windows.**  
> Full docs: `README.md` | API Reference: `docs/api_reference.md` | Design: `docs/architecture.md`

## What This Pack Does

Provides **production-grade quantitative trading capabilities** for AI Agents:

1. **Predict** — Multi-order causal reasoning for market events (whale moves, hacks, listings)
2. **Signal** — Generate standardized trading signals from technical, topological, chaos, and adversarial-RL models
3. **Validate** — Vectorized backtesting with institutional metrics (Sharpe, Sortino, Calmar, MaxDD)
4. **Execute** — Trade on CEX (CCXT) or DEX (Web3 + Flashbots MEV protection)
5. **Adapt** — Auto-export all skills as OpenAI/Anthropic function tools

## Quick Routing Table

| User Intent | Load Module | Key Class/Function |
|-------------|-------------|-------------------|
| "Predict what happens if..." | `skills/inference/` | `HigherOrderInferenceEngine.generate_prediction()` |
| "Analyze order book" | `skills/signals/technical/` | `OrderBookImbalance.generate()` |
| "Funding rate arbitrage" | `skills/signals/technical/` | `FundingArbitrageSignal.generate()` |
| "Detect FOMO/panic" | `skills/adversarial/` | `FOMODetector.detect()` |
| "Track whale wallet" | `skills/adversarial/` | `WhaleTracker.track()` |
| "Backtest strategy" | `backtest/` | `BacktestEngine.run()` |
| "Place order on Binance" | `skills/execution/connectors/` | `CCXTConnector.place_order()` |
| "Execute on-chain swap" | `skills/execution/web3/` | `Web3DEXExecutor.swap_exact_in()` |
| "Export to LLM tools" | `skills/agent/` | `AgentToolAdapter.export_openai_tools()` |

## Directory Loading Guide

**Load these at runtime** (essential):
- `skills/core/` — Types and registry
- `skills/inference/` — Causal reasoning
- `skills/signals/` — Signal generation
- `skills/execution/` — Order execution
- `skills/adversarial/` — Behavioral modeling
- `skills/agent/` — LLM tool adapter
- `backtest/` — Strategy validation

**Do NOT load these** (wastes tokens):
- `cli/` — npx installer (Node.js)
- `docs/` — Documentation site
- `examples/` — Demo scripts
- `scripts/` — Dev setup
- `tests/` — Unit tests
- `archive/` — Legacy code

## Agent Tool Schema

All skills expose `.run(context: dict)` for uniform dispatch.
Registry: `from skills.core import registry`

## Version

v3.0.0-S+ | MIT — VelonLabs
