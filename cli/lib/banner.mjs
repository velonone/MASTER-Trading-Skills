/**
 * VelonLabs Banner — borderless ALL-CAPS wordmark
 * ===================================================
 * Layout (no frame, just typography):
 *
 *      ██  ██  █████  ██      █████  ██  ██  ██      █████  █████  █████
 *      ██  ██  ██     ██      ██  ██ ██▓ ██  ██      ██  ██ ██  ██ ██
 *      ██  ██  ██     ██      ██  ██ ██████  ██      ██████ █████  █████
 *      ██  ██  ████   ██      ██▓▓██ ██████  ██      ██▓▓██ ██  ██     ██
 *       ████   ██     ██      ██▓▓██ ██ ███  ██      ██  ██ ██  ██     ██
 *        ██    █████  █████   █████  ██  ██  █████   ██  ██ █████  █████
 *
 *      M A S T E R    ·    T R A D I N G    ·    S K I L L S
 *      v3.1.0  ·  139 tests  ·  MIT  ·  calibration v2026.05
 *
 * Two-layer letterform (OpenCode-derived structure, our colours):
 *   - Outline cells `█` carry the row-gradient + horizontal sheen.
 *   - Inner-fill cells `▓` (encoded in FONT, rendered as full blocks)
 *     anchor to the deepest violet stop — high contrast against the
 *     outline so the layering reads even at small sizes.
 *
 * Animation: 1.6 s sheen sweep on truecolor TTYs, then settle. CI /
 * pipes / no-color terminals get a single static render.
 */

import {
  PALETTE,
  RESET,
  bold,
  dim,
  graphite,
  rgb,
  bgRgb,
  violet,
  violetSoft,
  GLYPHS,
  colorEnabled,
  supportsTrueColorOutput,
} from "./colors.mjs";

// ─────────────────────────── 6-row uppercase font ───────────────────────────
//
// Every glyph is 6 rows × 6 cols, 2-col strokes. "▓" marks inner-fill cells
// (the decorative dark block from OpenCode-style two-path layering).

const FONT = {
  V: [
    "██  ██",
    "██  ██",
    "██  ██",
    "██  ██",
    " ████ ",
    "  ██  ",
  ],
  E: [
    "██████",
    "██    ",
    "██    ",
    "████  ",
    "██▓▓  ",
    "██████",
  ],
  L: [
    "██    ",
    "██    ",
    "██    ",
    "██    ",
    "██▓▓  ",
    "██████",
  ],
  O: [
    "██████",
    "██  ██",
    "██  ██",
    "██▓▓██",
    "██▓▓██",
    "██████",
  ],
  N: [
    "██  ██",
    "███ ██",
    "██████",
    "██████",
    "██ ███",
    "██  ██",
  ],
  A: [
    " ████ ",
    "██  ██",
    "██████",
    "██▓▓██",
    "██  ██",
    "██  ██",
  ],
  B: [
    "█████ ",
    "██  ██",
    "█████ ",
    "██▓▓██",
    "██▓▓██",
    "█████ ",
  ],
  S: [
    "██████",
    "██    ",
    "█████ ",
    "    ██",
    "    ██",
    "██████",
  ],
  " ": [
    "      ",
    "      ",
    "      ",
    "      ",
    "      ",
    "      ",
  ],
};

const WORDMARK_TEXT = "VELONLABS";
const WORDMARK_GAP = 2;

function buildWordmark(text) {
  const rows = ["", "", "", "", "", ""];
  const sep = " ".repeat(WORDMARK_GAP);
  const chars = text.split("");
  chars.forEach((ch, idx) => {
    const glyph = FONT[ch] || FONT[" "];
    for (let r = 0; r < 6; r++) {
      rows[r] += glyph[r];
      if (idx < chars.length - 1) rows[r] += sep;
    }
  });
  return rows;
}

const WORDMARK_ROWS = buildWordmark(WORDMARK_TEXT);
const WORDMARK_WIDTH = WORDMARK_ROWS[0].length;

// ─────────────────────────── colour ramp ───────────────────────────

const RAMP = [
  [232, 220, 255], // 0 — highlight
  [200, 180, 255], // 1
  [160, 128, 255], // 2
  [124,  92, 255], // 3 — brand
  [ 88,  64, 212], // 4
  [ 58,  42, 143], // 5 — shadow
];

// Inner-fill anchor: even darker than RAMP[5] so the layering pops.
const INNER_FILL_BASE = [28, 14, 70];   // very deep violet, near-black
const INNER_FILL_LIFT = [60, 36, 120];  // slight breathing toward this

const lerp = (a, b, t) => a + (b - a) * t;
const mix = (a, b, t) => [
  Math.round(lerp(a[0], b[0], t)),
  Math.round(lerp(a[1], b[1], t)),
  Math.round(lerp(a[2], b[2], t)),
];

function outlineColor(rowIdx, col, rowLen, frame) {
  const baseStop = rowIdx;
  const sheen = Math.sin((col / rowLen) * Math.PI * 2 + frame * 0.16);
  const fStop = Math.max(0, Math.min(RAMP.length - 1, baseStop - sheen * 0.7));
  const lo = Math.floor(fStop);
  const hi = Math.min(RAMP.length - 1, lo + 1);
  return mix(RAMP[lo], RAMP[hi], fStop - lo);
}

function innerFillColor(col, rowLen, frame) {
  const sheen = Math.sin((col / rowLen) * Math.PI * 2 + frame * 0.16);
  // Mostly INNER_FILL_BASE; subtle 30 % lift on bright sheen pass.
  const t = Math.max(0, Math.min(1, (1 + sheen) * 0.15));
  return mix(INNER_FILL_BASE, INNER_FILL_LIFT, t);
}

function colorizeWordmark(rows, frame) {
  if (!colorEnabled) return rows.map((r) => r.replace(/▓/g, "█"));
  return rows.map((row, rowIdx) => {
    let out = "";
    for (let col = 0; col < row.length; col++) {
      const ch = row[col];
      if (ch === " ") { out += ch; continue; }
      if (ch === "▓") {
        out += rgb(innerFillColor(col, row.length, frame)) + "█" + RESET;
        continue;
      }
      out += rgb(outlineColor(rowIdx, col, row.length, frame)) + ch + RESET;
    }
    return out + RESET;
  });
}

// ─────────────────────────── escape-aware width ───────────────────────────

function visibleLength(str) {
  // eslint-disable-next-line no-control-regex
  return str.replace(/\x1b\[[0-9;]*m/g, "").length;
}

// ─────────────────────────── subtitle ───────────────────────────

function subtitleRows({ version, calibrationVersion, testCount = 139 }) {
  const dot = graphite("    ·    ");
  const tagline =
    bold(violet("M A S T E R")) + dot +
    bold(violet("T R A D I N G")) + dot +
    bold(violet("S K I L L S"));
  const status = [
    `v${version}`,
    `${testCount} tests`,
    `MIT`,
    `calibration v${calibrationVersion}`,
  ].map((s) => violetSoft(s)).join(graphite("  ·  "));
  return [tagline, status];
}

// ─────────────────────────── frame composition ───────────────────────────
//
// No border. Each line gets a 4-space left indent so the wordmark
// breathes against the terminal edge.

const INDENT = "    ";

function composeFrameLines({ wordmarkColored, subtitle }) {
  const lines = [""];
  for (const r of wordmarkColored) {
    lines.push(INDENT + r);
  }
  lines.push("");
  for (const s of subtitle) {
    lines.push(INDENT + s);
  }
  lines.push("");
  return lines;
}

// ─────────────────────────── animation primitives ───────────────────────────

const HIDE_CURSOR = colorEnabled ? "\x1b[?25l" : "";
const SHOW_CURSOR = colorEnabled ? "\x1b[?25h" : "";
const ERASE_LINE  = colorEnabled ? "\x1b[2K"  : "";
const moveUp = (n) => (n > 0 && colorEnabled ? `\x1b[${n}A` : "");
const moveCol1 = colorEnabled ? "\x1b[G" : "";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ─────────────────────────── public API ───────────────────────────

export async function animateBanner({
  version = "?",
  calibrationVersion = "?",
  testCount = 139,
  durationMs = 1600,
  fps = 18,
} = {}) {
  const subtitle = subtitleRows({ version, calibrationVersion, testCount });

  if (!colorEnabled || !supportsTrueColorOutput || !process.stdout.isTTY) {
    const colored = colorizeWordmark(WORDMARK_ROWS, 0);
    const lines = composeFrameLines({ wordmarkColored: colored, subtitle });
    process.stdout.write(lines.join("\n") + "\n");
    return;
  }

  process.stdout.write(HIDE_CURSOR);

  const totalFrames = Math.max(8, Math.floor((durationMs / 1000) * fps));
  const interval = 1000 / fps;

  let lines = composeFrameLines({
    wordmarkColored: colorizeWordmark(WORDMARK_ROWS, 0),
    subtitle,
  });
  process.stdout.write(lines.join("\n") + "\n");
  const totalRows = lines.length;

  for (let f = 1; f < totalFrames; f++) {
    await sleep(interval);
    process.stdout.write(moveUp(totalRows) + moveCol1);
    lines = composeFrameLines({
      wordmarkColored: colorizeWordmark(WORDMARK_ROWS, f),
      subtitle,
    });
    process.stdout.write(lines.map((l) => ERASE_LINE + l).join("\n") + "\n");
  }

  process.stdout.write(moveUp(totalRows) + moveCol1);
  lines = composeFrameLines({
    wordmarkColored: colorizeWordmark(WORDMARK_ROWS, 0),
    subtitle,
  });
  process.stdout.write(lines.map((l) => ERASE_LINE + l).join("\n") + "\n");

  process.stdout.write(SHOW_CURSOR);
}

export function renderBanner(opts = {}) {
  const subtitle = subtitleRows({
    version: opts.version || "?",
    calibrationVersion: opts.calibrationVersion || "?",
    testCount: opts.testCount || 139,
  });
  const colored = colorizeWordmark(WORDMARK_ROWS, 0);
  const lines = composeFrameLines({ wordmarkColored: colored, subtitle });
  return lines.join("\n");
}

// ─────────────────────────── ceremony rail ───────────────────────────

export class Ceremony {
  constructor(tag = "master-trading") {
    this.tag = tag;
    this._opened = false;
  }
  rail(extra = "") {
    return graphite(GLYPHS.treeVert) + (extra ? "  " + extra : "");
  }
  section(label, sub = "") {
    if (this._opened) console.log(this.rail());
    this._opened = true;
    console.log(violet(GLYPHS.diamond) + "  " + bold(label));
    if (sub) for (const line of String(sub).split("\n")) console.log(this.rail("  " + graphite(line)));
  }
  field(key, value) {
    console.log(this.rail(`  ${graphite(String(key).padEnd(12, " "))} ${value}`));
  }
  line(text = "") {
    if (text === "") console.log(this.rail());
    else for (const l of String(text).split("\n")) console.log(this.rail("  " + l));
  }
  status(label, kind = "done") {
    const map = {
      done: rgb(PALETTE.success) + GLYPHS.check + RESET,
      running: violet("◐"),
      skip: graphite(GLYPHS.dash),
      fail: rgb(PALETTE.danger) + GLYPHS.cross + RESET,
    };
    console.log(this.rail(`  ${map[kind] || map.done} ${label}`));
  }
  tagPill() {
    if (!colorEnabled) { console.log(`[${this.tag}]\n`); return; }
    console.log(bgRgb(PALETTE.violet) + " " + bold(`[${this.tag}]`) + " " + RESET);
    console.log("");
  }
  close() { console.log(this.rail()); }
}
