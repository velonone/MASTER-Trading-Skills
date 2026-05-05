# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] — 2026-05-05

### Added — Open-Source Hardening Release

#### Calibration system (new)
- `skills/inference/calibration.py` — `Calibration` class with resolve / persist /
  freshness logic and a CLI (`python -m skills.inference …`).
- `skills/inference/_calibration_data.py` — bundled **VelonLabs Reference
  Calibration v2026.05** (real values, not placeholders).
- `skills/inference/setup_skill.py` — `CalibrationSetupSkill` so any LLM agent
  can configure the source through the standard tool-dispatch interface.
- Every inference output now carries a `_meta` block with calibration source,
  version, age, and freshness warning for audit traceability.

#### Agent safety surface
- `AgentToolAdapter` now accepts an `AgentPolicy` and enforces capability
  tier (`read` / `signal` / `risk` / `trade`), blocklist, and daily budget
  before dispatch. Each call appends to an in-memory + structured-log
  audit trail.
- Added `agent.audit` logger emitting policy decisions and tool outcomes.

#### Trading pipeline (new)
- `skills.execution.TradingPipeline` — minimal Signal → Risk → OMS →
  Connector orchestrator. One call, full audit per step.
- `OrderManagementSystem.to_snapshot` / `save` / `from_file` for
  crash-recovery state persistence.

#### Backtest correctness
- Eliminated lookahead bias: signals now generated on bar `t-1`, fills on
  bar `t` open. Added `test_backtest_no_lookahead_oracle_strategy`
  regression test.

#### OMS realized PnL
- Long-close, short-close, partial-close, and flip branches all corrected.
  Five new regression tests cover each path.

#### Schema and connectors
- `SkillSchemaGenerator` now correctly maps `Optional[T]`, `Decimal`,
  `Literal[...]`, `Enum` subclasses, and typed `List[T]`.
- `CCXTConnector._client` made thread-safe with double-checked
  `asyncio.Lock`.

#### Web3 DEX executor
- `Web3DEXExecutor.swap_exact_in` requires explicit
  `allow_stub_swap=True` to return the placeholder hash, preventing
  silent fake fills in production.

#### Brand kit + governance
- `docs/assets/brand/` — VelonLabs brand kit: SVG mark (light/dark
  variants), wordmark, banner, color tokens, typography, lockup rules.
  `BRAND.md` documents reuse for downstream VelonLabs projects.
- README rewritten with logo-left / text-right header, Disclaimer,
  Calibration, Attribution, and About-VelonLabs sections.
- `CONTRIBUTING.md` rewritten with hard rules (no secrets, no private
  calibration), branch naming, conventional commits, review tiers,
  calibration-update workflow.
- `.github/PULL_REQUEST_TEMPLATE.md` and three `ISSUE_TEMPLATE/`
  templates (bug, feature, calibration_update).

#### NPX installer
- Banner rewritten — drops self-rating language, dynamically reads
  package version, surfaces the bundled calibration version.
- Adds risk disclaimer block and calibration-setup pointer at the end
  of every install.
- Manifest now records `installerVersion`, `calibration`, and
  `attribution` for downstream auditing.

### Tests
- 113 → 139 tests passing (+26 calibration tests, +5 OMS PnL,
  +5 agent policy, +5 schema typing, +5 pipeline integration,
  +1 backtest lookahead regression, +1 web3 stub guard).

### Removed
- "S+ Grade / S+ Certified" self-rating language across README, banner,
  package metadata.
- Outdated test count badge (was 57, now 139).

### Security
- Logging in `agent.adapter`, `execution.risk`, `execution.oms`,
  `execution.web3`, `execution.pipeline` to `master.*` namespace via
  `skills.core.logging.get_logger`.
- `~/.master-trading/config.json` written with `chmod 0600`.
- `.gitignore` now blocks `.claude/`, `.cursor/`, `.qoder/`,
  `.master-trading/`, `*.calibration.json`, `trades_*.csv`.

---

## [3.0.0-S+] — 2026-05-05

### Added — S+ Upgrade
- **Vectorized Backtest Engine** (`backtest/`)
  - `BacktestEngine` for high-performance bar-by-bar strategy simulation
  - `BrokerSimulator` with market and limit order fill modeling
  - `VolatilitySlippage` model based on Almgren-Chriss market impact
  - Institutional-grade metrics: Sharpe, Sortino, Calmar, Max Drawdown, Profit Factor
- **Web3 DEX Executor** (`skills/execution/web3/`)
  - `Web3DEXExecutor` with async Web3.py v7 integration
  - `MEVProtection` supporting Flashbots Protect, MEV Blocker, and Eden Network
  - EIP-1559 dynamic gas estimation and transaction lifecycle management
- **LLM Agent Tool Adapter** (`skills/agent/`)
  - `AgentToolAdapter` for OpenAI Functions and Anthropic Tool Use
  - `SkillSchemaGenerator` for automatic JSON Schema generation from Pydantic models
  - Context-window truncation guards for large outputs
- **DevOps & Quality**
  - GitHub Actions CI with Python 3.11/3.12 matrix
  - 57 unit tests across all modules
  - `pyproject.toml` with `[dev]` and `[security]` extras
  - ruff, black, mypy strict mode configuration

### Changed
- Refactored entire project from document-driven to code-first architecture
- Unified all skill outputs to `skills.core.types.Signal` schema
- Replaced fragmented sub-skills with clean module hierarchy
- All terminology standardized to English professional vocabulary

### Removed
- Legacy `.zip` and `.skill` binary artifacts
- Deprecated nested directory structures
- Unused `__pycache__` and build artifacts

## [2.0.0] — 2025-11 (Legacy)

### Added
- Initial Trinity Weapon System architecture documentation
- Higher-order trading inference framework (document-only)
- PROACTIVE TRIGGER CONDITIONS with TDA, chaos theory, and adversarial RL references
- Financial agent adversarial intelligence module (document-only)

## [1.0.0] — 2025-06 (Legacy)

### Added
- Master trading skill pack initialization
- Quant trading masterclass reference documents
- Web3 advanced engineering directory structure
- Grandmaster paradigm cognitive framework
