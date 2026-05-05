---
name: Calibration update proposal
about: Propose a change to the bundled VelonLabs Reference Calibration
title: "[calibration] "
labels: ["calibration", "needs-triage"]
assignees: []
---

> **Read this first.** The bundled snapshot in
> `skills/inference/_calibration_data.py` is a curated artifact, not
> an open editing surface. Do not open a PR until this issue has been
> accepted by a maintainer. See
> [CONTRIBUTING.md › Updating the reference calibration](../../CONTRIBUTING.md#updating-the-reference-calibration).

## Which value(s)?

<!--
Identify the exact key path: e.g.
- primitives.whale_exchange_deposit.base_confidence
- causal_chains.whale.exchange_deposit[0].confidence
- signal_thresholds.buy_above
- singularity_weights.has_leverage_exposure
-->

| Key path | Current value | Proposed value |
|---|---|---|
|   |   |   |

## Empirical justification

<!--
Required. Describe the evidence: data window, methodology, sample size,
and what changed in the market that motivates the update.
-->

- Data window:
- Methodology:
- Sample size / number of events:
- Out-of-sample validation:

## Plots / numbers

<!-- Attach charts, link to a notebook, or paste a results table. -->

## Risks

<!--
What goes wrong if we ship this change? Who is most affected
(snapshot users, self-calibration users, custom JSON users)?
-->

## Proposed snapshot version bump

- From: `2026.05`
- To: `2026.??`
- Estimated `released_at`:

---

*Submitting this proposal does not constitute permission to open a PR.
A maintainer will respond with accept / defer / reject.*
