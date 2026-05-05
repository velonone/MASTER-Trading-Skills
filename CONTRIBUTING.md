# Contributing to master-trading-skills

Thanks for taking the time to contribute. This guide covers everything
from environment setup to the rules around calibration data and
sensitive material — please read at least the "Hard rules" section
before opening a PR.

> Maintained by **VelonLabs**.
> Brand assets and visual guidelines: [`docs/assets/brand/BRAND.md`](docs/assets/brand/BRAND.md).

---

## Hard rules (read first)

These are non-negotiable — PRs that violate them will be closed.

1. **Never commit secrets.** No API keys, private keys, mnemonic phrases,
   `.env` files, OAuth tokens, exchange credentials, or RPC URLs that
   include auth tokens. We use `.gitignore` to block the obvious cases,
   but the responsibility is yours.

2. **Never commit private calibration data.**
   The only calibration file that lives in this repo is the public
   reference snapshot at
   [`skills/inference/_calibration_data.py`](skills/inference/_calibration_data.py).
   All other calibrations — VelonLabs internal data, your own
   self-calibration JSON files — must stay outside the repo.
   `.gitignore` blocks the standard patterns (`*.calibration.json`,
   `calibration_*.json`, `trades_*.csv`, `~/.master-trading/`); do not
   bypass it.

3. **Never commit real trade history or PnL data**, even anonymised.
   Use synthetic data for tests; if you need a fixture, generate it
   from a seeded RNG.

4. **Don't change calibration values speculatively.** The reference
   snapshot is treated as a curated artifact — see
   [Updating the reference calibration](#updating-the-reference-calibration).

5. **Don't bypass the policy gate or audit log in
   `skills/agent/`** without explicit maintainer approval. These two
   surfaces are the safety boundary for LLM-driven trading; weakening
   them is a breaking change even when no test fails.

6. **Never weaken or remove the disclaimer** in `README.md` or the
   risk-acknowledgement block in the `cli/install.mjs` installer.

---

## Development Setup

```bash
# 1. Fork and clone (replace with your fork URL)
git clone https://github.com/YOUR_USERNAME/master-trading-skills.git
cd master-trading-skills

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\activate           # Windows PowerShell

# 3. Install in editable mode with dev dependencies
pip install -e ".[dev]"

# 4. (Optional) install Web3 / security extras
pip install -e ".[security]"

# 5. Run the test suite — should be all green
pytest -q

# 6. Run lint + type check
ruff check skills backtest tests
mypy skills backtest --ignore-missing-imports
```

Calibration is auto-resolved to the bundled snapshot during development.
You can switch to placeholder mode for fast unit-test iteration:

```bash
export MASTER_TRADING_CALIBRATION=placeholder
```

---

## Project layout

```
skills/
├── core/             Universal types & base classes — review-required
├── agent/            LLM tool adapter, AgentPolicy, schema   — review-required
├── inference/        Causal reasoning + calibration system   — review-required
├── execution/        Risk, OMS, pipeline, CCXT, Web3
├── signals/          Signal generators (technical, advanced math)
├── adversarial/      Behavioural / opponent modelling
backtest/             Vectorised backtest engine + slippage
tests/                pytest suite — mirrors source layout
tests/integration/    Cross-module integration tests
docs/                 Markdown docs + brand assets
docs/assets/brand/    Logos, tokens, lockups, BRAND.md
cli/                  npx installer (Node.js)
examples/             Runnable demos
tools/                Utilities (calibrate.py, etc.)
```

Modules tagged **review-required** above touch the safety surface
(types, agent policy, calibration). Changes need a second maintainer
to ack — see [Review tiers](#review-tiers).

---

## Branch naming

| Prefix | When to use | Example |
|---|---|---|
| `feat/`     | New feature, new skill, new public API           | `feat/topological-regime-detector`     |
| `fix/`      | Bug fix or incorrect behaviour                   | `fix/oms-short-pnl-sign`               |
| `docs/`     | README, docstrings, tutorials, BRAND.md          | `docs/calibration-quickstart`          |
| `test/`     | Test-only additions or fixtures                  | `test/pipeline-edge-cases`             |
| `refactor/` | Internal restructuring, no behaviour change      | `refactor/extract-calibration-module`  |
| `perf/`     | Measurable performance improvement               | `perf/vectorise-broker-fill`           |
| `chore/`    | Build, CI, dependencies, formatting              | `chore/bump-pydantic`                  |
| `security/` | Security fixes                                   | `security/redact-private-key-logs`     |

Avoid generic names like `update`, `improve`, or anything starting with
your own initials.

---

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(execution): add TradingPipeline orchestrator
fix(oms): correct realized PnL on short close
docs(brand): document logo lockup variants
test(calibration): cover env-var precedence
chore(ci): bump pytest to 9.0
```

Keep the subject under 72 characters. Use the body for the *why*; the
diff already shows *what*.

---

## Coding standards

### Python style
- Formatter: **black** (line length 100)
- Linter: **ruff**
- Type checker: **mypy** (strict where practical)
- Python: **3.11+** with modern syntax (`|`, `match`, `async`)

### Types
- All public functions need type annotations.
- Pydantic v2 models for all data structures.
- No `Any` unless documented why.

### Docstrings
- Google-style for all public modules, classes, and methods.
- Cite a paper / DOI / arXiv ID when implementing a known method.

### Testing
- pytest for everything.
- Async tests via `pytest.mark.asyncio` (mode is auto in `pyproject.toml`).
- Aim ≥90% coverage for new code.
- New numerical code: include a regression test that pins behaviour.
- Integration tests live under `tests/integration/`.

### Logging
- Use `skills.core.logging.get_logger(__name__)`. No `print()`.
- Log lines should be structured key=value to stay grep-friendly.

---

## Review tiers

| Surface | Reviewers required |
|---|---|
| `skills/core/`, `skills/agent/`, `skills/inference/calibration.py`, installer disclaimer/policy gate | **2 maintainers** |
| `skills/execution/`, `backtest/`, `skills/signals/`, `skills/adversarial/`         | 1 maintainer        |
| `docs/`, `examples/`, `tests/`, `cli/lib/`, brand assets                          | 1 maintainer        |

If your PR touches a tier-2 file plus any tier-1 file, the higher tier
applies.

---

## Updating the reference calibration

The bundled snapshot in `_calibration_data.py` is a **curated artifact**,
not an open editing surface. To change a value:

1. Open an issue first describing what you want to change and why.
2. Include empirical justification (links, plots, time periods).
3. The maintainer team will respond with one of:
   - Accept → bump the snapshot version (e.g. `2026.05` → `2026.06`)
     and update `released_at`. Submit the PR with the issue linked.
   - Defer → goes into the next scheduled calibration release.
   - Reject → reasoning posted to the issue.

Do **not** open a calibration-change PR without an accepted issue.

---

## Adding a new skill

Skills inherit from one of the base classes and emit standardized
types so the Agent runtime can dispatch them uniformly.

```python
from skills.core.base import BaseStrategy
from skills.core.types import Signal, SignalAction


class MyNewStrategy(BaseStrategy):
    name = "my_new_strategy"
    description = "One-line description of what this skill does."
    version = "1.0.0"

    def generate_signals(self, context: dict) -> list[Signal]:
        return [Signal(
            action=SignalAction.BUY,
            confidence=0.85,
            strength=0.7,
            symbol=context["symbol"],
            source=self.name,
            evidence=["Reason for signal"],
        )]
```

Checklist:

- [ ] Inherits from `BaseStrategy`, `BaseRiskManager`, or `BaseConnector`.
- [ ] Implements all abstract methods.
- [ ] Tests under `tests/test_<module>.py`.
- [ ] Added to `SKILL.md` skill inventory if user-facing.
- [ ] Numerical defaults are explicitly justified in the docstring.

---

## Reporting security issues

Do **not** open a public issue for security findings. Email the
maintainers per [`SECURITY.md`](SECURITY.md). Sensitive findings
include private-key handling, agent policy bypass, secret leakage,
and remote code execution paths.

---

## Code of Conduct

We follow the contributor covenant — see [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
TL;DR: be respectful, focus on the work, no harassment.

---

## Questions

- General discussion: open a [Discussion](https://github.com/velonone/MASTER-Trading-Skills/discussions).
- Bugs / feature requests: open an [Issue](https://github.com/velonone/MASTER-Trading-Skills/issues)
  using the appropriate template.
- Brand / attribution / commercial inquiries: see
  [`docs/assets/brand/BRAND.md`](docs/assets/brand/BRAND.md).
