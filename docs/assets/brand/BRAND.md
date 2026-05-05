# VelonLabs Brand Kit

This directory holds every visual asset used by `master-trading-skills`
and is intended to be reused across other VelonLabs open-source
projects, documentation, and social channels.

> Maintainer: VelonLabs Brand · Latest revision: 2026-05

---

## Asset Map

| File | Purpose | Format | Status |
|---|---|---|---|
| `velonlabs-icon.png`             | **Primary mark** — official VelonLabs interlocking V/N. Used everywhere downstream (README, docs, NPM card). | PNG (square) | ✓ official |
| `velonlabs-mark-light.svg`       | Placeholder light variant (for dark backgrounds). Drop the official SVG over this when ready; the filename is referenced by docs. | SVG | placeholder |
| `velonlabs-mark-dark.svg`        | Placeholder dark variant (for light backgrounds). | SVG | placeholder |
| `velonlabs-wordmark.svg`         | Placeholder mark + "VELONLABS" wordmark. Horizontal lockup for narrow contexts. | SVG | placeholder |
| `velonlabs-banner.svg`           | Placeholder mark + product name + tagline. Future README banner / social card. | SVG | placeholder |

The README and About-VelonLabs section use `velonlabs-icon.png` directly
because it is the only file that carries the official mark. The SVG
placeholders are kept for future variants (light/dark, wordmark, banner)
and downstream projects that want to wire up the same lockup pattern; replace
them with official designer files whenever ready and nothing else has to
change in consumer code.

---

## Color Tokens

| Token | Hex | RGB | Usage |
|---|---|---|---|
| `--velon-violet`        | `#7C5CFF` | 124, 92, 255 | Primary brand color. The interlocking VL mark. |
| `--velon-violet-deep`   | `#5840D4` | 88, 64, 212  | Hover/active states, deeper accents. |
| `--velon-violet-soft`   | `#B5A3FF` | 181, 163, 255 | Backgrounds, halftone dots. |
| `--velon-ink`           | `#0A0A14` | 10, 10, 20   | Body text on light backgrounds; dark surface base. |
| `--velon-paper`         | `#FAFAFC` | 250, 250, 252 | Light surface base. |
| `--velon-graphite`      | `#52526B` | 82, 82, 107  | Secondary text, captions. |
| `--velon-success`       | `#28C76F` | 40, 199, 111 | Pass/OK states. |
| `--velon-warning`       | `#FFB547` | 255, 181, 71 | Warnings. |
| `--velon-danger`        | `#FF4D6D` | 255, 77, 109 | Risks / disclaimers. |

Pair `velon-violet` with `velon-ink` (dark mode) or `velon-paper` (light mode).
**Never** put `velon-violet` directly on `velon-violet-soft` — too low contrast.

---

## Typography

- **Display / headings**: `Inter`, fall back to `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`
- **Body**: same stack
- **Monospace** (code, terminal output, calibration metadata):
  `JetBrains Mono`, fall back to `ui-monospace, SFMono-Regular, "Cascadia Code", Menlo, monospace`

In Markdown contexts (GitHub, npm) the system stack is sufficient — do not
ship custom fonts inside the repo.

---

## Logo Usage Rules

**Do**
- Maintain at least 16px of clear space around the mark.
- Use the SVG variants for any digital surface; PNG only for legacy contexts.
- Pair the mark with the product name on its right (see `velonlabs-banner.svg`).
- Use `velonlabs-mark-light.svg` on backgrounds darker than `#404060`.

**Don't**
- Recolor the mark. The violet is the brand.
- Stretch, rotate, or skew. The geometry is the identity.
- Place on busy photographs without a solid plate behind it.
- Combine with another logo without a vertical divider and 32px gap.

---

## Lockups

### Horizontal (default for README, docs, npm card)

```
┌──────┐  ┌──────────────────────────────────────────┐
│      │  │  master-trading-skills                   │
│ MARK │  │  Open-source trading skills · VelonLabs  │
│      │  │                                          │
└──────┘  └──────────────────────────────────────────┘
   ↑ 96px square    ↑ vertically centered, 24px gap
```

### Stacked (for square cards, badges)

```
       ┌──────┐
       │ MARK │
       └──────┘
    velon labs
```

### Wordmark only (when space is tight)

```
[mark]VELONLABS
```

---

## Attribution Snippet

When the brand is used in third-party docs, research papers, or commercial
products built on top of `master-trading-skills`, include this line:

> Powered by **VelonLabs Trading Skills** — open-source trading skills
> for AI agents. <https://github.com/velonone/MASTER-Trading-Skills>

The phrase **"VelonLabs Reference Calibration"** also appears in every
inference output's `_meta` block; downstream consumers should preserve
that string when persisting or visualizing model outputs.

---

## Reusing this kit on other VelonLabs projects

1. Copy the entire `docs/assets/brand/` directory.
2. Update only the `<product name>` and tagline on `velonlabs-banner.svg`.
3. Keep `BRAND.md` verbatim — it is the source of truth for color tokens
   and rules. Diverging projects fragment the brand.

---

## File provenance

| File | Status |
|---|---|
| `BRAND.md`                  | this file (source of truth) |
| `velonlabs-icon.png`        | official VelonLabs primary mark, dropped in 2026-05-05 |
| `velonlabs-mark-light.svg`  | placeholder — replace with official light variant |
| `velonlabs-mark-dark.svg`   | placeholder — replace with official dark variant |
| `velonlabs-wordmark.svg`    | placeholder — replace with official wordmark |
| `velonlabs-banner.svg`      | placeholder — replace with official banner |

The official PNG is used everywhere a mark is needed today. The
remaining SVG placeholders are kept under the documented filenames so
downstream consumers don't break when the official SVG variants are
dropped in.
