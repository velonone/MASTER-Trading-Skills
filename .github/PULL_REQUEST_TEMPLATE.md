<!--
Thank you for the PR. Please fill in every section. Empty sections will
slow review. See CONTRIBUTING.md for the hard rules and review tiers.
-->

## Summary

<!-- One paragraph: what this PR does and why. -->

## Type of change

- [ ] feat — new feature / new skill / new public API
- [ ] fix — bug fix
- [ ] docs — README, docstrings, BRAND.md, tutorials
- [ ] test — test-only additions
- [ ] refactor — internal change, no behaviour difference
- [ ] perf — measurable performance improvement
- [ ] security — security fix
- [ ] chore — build / CI / dependencies

## Scope

Which surfaces does this PR touch? (check all that apply)

- [ ] `skills/core/`        *(tier-1, 2 reviewers)*
- [ ] `skills/agent/`       *(tier-1, 2 reviewers — policy / audit)*
- [ ] `skills/inference/`   *(tier-1, 2 reviewers — calibration)*
- [ ] `skills/execution/`
- [ ] `skills/signals/`
- [ ] `skills/adversarial/`
- [ ] `backtest/`
- [ ] `cli/` / npx installer
- [ ] `docs/` / README / BRAND.md
- [ ] `tests/`
- [ ] `tools/`

## Hard-rule checklist

- [ ] No secrets committed (API keys, private keys, tokens, `.env`)
- [ ] No private calibration data committed
- [ ] No real trade history or PnL data committed
- [ ] If touching `_calibration_data.py`: linked to an accepted calibration-update issue
- [ ] If touching `skills/agent/adapter.py` or `policy.py`: maintainer pre-acknowledged
- [ ] Disclaimer in `README.md` and installer is intact

## Tests

- [ ] All existing tests pass (`pytest -q`)
- [ ] New code has tests
- [ ] Tests live under `tests/` mirroring source layout
- [ ] Numerical changes include a regression test pinning the new behaviour

## Documentation

- [ ] Updated `README.md` if a public API changed
- [ ] Updated `SKILL.md` if a skill was added / removed / renamed
- [ ] Updated `CHANGELOG.md`
- [ ] Updated docstrings for any new/changed public function

## Risk + reversibility

<!--
Briefly: what's the worst that could happen if this lands and is wrong?
For trading-relevant changes, describe how a user would discover the
problem and how to roll back.
-->

## Linked issues

<!-- Closes #123, refs #456 -->

---

*By submitting this PR I confirm I have read [CONTRIBUTING.md](../CONTRIBUTING.md)
and agree my contribution is licensed under the project's MIT license.*
