# VelonLabs Brand Kit

This directory holds every visual asset used by `master-trading-skills`
and is intended to be reused across other VelonLabs open-source
projects, documentation, and social channels.

> Maintainer: VelonLabs Brand · Latest revision: 2026-05

---

## Asset Map

| File | Purpose | Format | Min size | Background |
|---|---|---|---|---|
| `velonlabs-mark.svg`            | The mark only (geometric "VL" interlock). Square. | SVG | 32×32 | Transparent |
| `velonlabs-mark-light.svg`      | Mark for use on dark surfaces (light fill).       | SVG | 32×32 | Transparent |
| `velonlabs-mark-dark.svg`       | Mark for use on light surfaces (dark fill).       | SVG | 32×32 | Transparent |
| `velonlabs-wordmark.svg`        | Mark + "VELONLABS" text. Horizontal lockup.       | SVG | 200×60 | Transparent |
| `velonlabs-banner.svg`          | Mark + product name + tagline. README-ready.      | SVG | 1200×300 | Transparent |
| `velonlabs-social-card.png`     | GitHub/Twitter social preview.                    | PNG | 1280×640 | Brand purple |
| `favicon.ico` / `favicon-32.png`| Docs site favicon.                                | ICO/PNG | 32×32 | Transparent |

If you only have time to ship two files: `velonlabs-mark-light.svg` and
`velonlabs-mark-dark.svg`. The README uses `<picture>` to pick whichever
matches the viewer's GitHub theme.

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
| `BRAND.md` | this file |
| `velonlabs-mark-placeholder.svg` | bundled placeholder rendered from spec |
| All other assets | **TODO** — to be replaced with official VelonLabs designer files |

The placeholder mark is sized and colored to the spec above. Drop the
official SVG over it whenever ready; nothing else has to change because
all consumers reference filenames, not contents.
