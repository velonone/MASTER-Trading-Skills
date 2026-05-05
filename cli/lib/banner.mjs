/**
 * Animated VelonLabs Banner — bold embossed wordmark
 * =====================================================
 * The previous wordmark used 1-col strokes which read as thin and
 * fragile. This pass thickens every stroke to 2 columns and grows
 * the letterform to 6 rows tall — same Opencode-style emboss, but
 * with the visual weight of a stamped metal logo.
 *
 *     ╭──────────────────────────────────────────────────────────────────────────╮
 *     │                                                                          │
 *     │     ██   ██  ██████  ██      ██████  ██   ██  ██      █████   █████      │ ← bright (top edge)
 *     │     ██   ██  ██      ██      ██  ██  ███  ██  ██      ██  ██  ██  ██     │
 *     │     ██   ██  ████    ██      ██  ██  ██ █ ██  ██      ██████  ██████     │ ← brand
 *     │     ██   ██  ██      ██      ██  ██  ██ ████  ██      ██  ██  ██  ██     │
 *     │      ██ ██   ██      ██      ██  ██  ██  ███  ██      ██  ██  ██  ██     │
 *     │       ███    ██████  ██████  ██████  ██   ██  ██████  ██  ██  █████      │ ← shadow (bottom)
 *     │                                                                          │
 *     │            M A S T E R    ·    T R A D I N G    ·    S K I L L S         │
 *     │       v3.1.0 · 139 tests · MIT · calibration v2026.05                    │
 *     │                                                                          │
 *     ╰──────────────────────────────────────────────────────────────────────────╯
 *
 * Depth (虚实感):
 *   - 6-stop violet ramp: highlight #E5DAFF → shadow #3A2A8F
 *   - Horizontal sheen sweeps ±1 ramp stop with sin(col + frame), so a
 *     soft highlight rolls across the letters during the 1.6 s startup
 *     animation, then settles to the canonical embossed frame.
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

// ─────────────────────────── 6-row block font ───────────────────────────
//
// Each glyph is exactly 6 rows tall × 6 columns wide. Strokes are 2
// columns thick so the type reads as bold without needing a wider
// canvas. Letter spacing is 2 columns of breathing room.

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
    "█████ ",
    "██    ",
    "██    ",
    "██████",
  ],
  L: [
    "██    ",
    "██    ",
    "██    ",
    "██    ",
    "██    ",
    "██████",
  ],
  O: [
    "██████",
    "██  ██",
    "██  ██",
    "██  ██",
    "██  ██",
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
    "██  ██",
    "██████",
    "██  ██",
    "██  ██",
  ],
  B: [
    "█████ ",
    "██  ██",
    "█████ ",
    "██  ██",
    "██  ██",
    "█████ ",
  ],
  S: [
    "██████",
    "██    ",
    "██████",
    "    ██",
    "    ██",
    "██████",
  ],
  M: [
    "█    █",
    "██  ██",
    "██████",
    "██████",
    "██  ██",
    "██  ██",
  ],
  T: [
    "██████",
    "  ██  ",
    "  ██  ",
    "  ██  ",
    "  ██  ",
    "  ██  ",
  ],
  R: [
    "█████ ",
    "██  ██",
    "█████ ",
    "█████ ",
    "██  ██",
    "██  ██",
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
const WORDMARK_GAP = 2; // cols of breathing room between glyphs

function buildWordmark(text) {
  const rows = ["", "", "", "", "", ""];
  const sep = " ".repeat(WORDMARK_GAP);
  const chars = text.split("");
  chars.forEach((ch, idx) => {
    const glyph = FONT[ch.toUpperCase()] || FONT[" "];
    for (let r = 0; r < 6; r++) {
      rows[r] += glyph[r];
      if (idx < chars.length - 1) rows[r] += sep;
    }
  });
  return rows;
}

const WORDMARK_ROWS = buildWordmark(WORDMARK_TEXT);
const WORDMARK_HEIGHT = WORDMARK_ROWS.length;

// ─────────────────────────── box dimensions ───────────────────────────

const BOX_WIDTH = 86;                 // bumped from 76 to host the bolder type
const INNER_WIDTH = BOX_WIDTH - 4;

// ─────────────────────────── 6-stop violet ramp ───────────────────────────

const RAMP = [
  [232, 220, 255], // 0 — near-white highlight
  [200, 180, 255], // 1 — light
  [160, 128, 255], // 2 — light-mid
  [124,  92, 255], // 3 — brand violet
  [ 88,  64, 212], // 4 — violetDeep
  [ 58,  42, 143], // 5 — shadow
];

const lerp = (a, b, t) => a + (b - a) * t;

function mix(a, b, t) {
  return [
    Math.round(lerp(a[0], b[0], t)),
    Math.round(lerp(a[1], b[1], t)),
    Math.round(lerp(a[2], b[2], t)),
  ];
}

function cellColor(rowIdx, col, rowLen, frame) {
  const baseStop = rowIdx; // 0..5, perfectly aligned with RAMP indices
  const sheen = Math.sin((col / rowLen) * Math.PI * 2 + frame * 0.16);
  const fStop = Math.max(0, Math.min(RAMP.length - 1, baseStop - sheen * 0.7));
  const lo = Math.floor(fStop);
  const hi = Math.min(RAMP.length - 1, lo + 1);
  return mix(RAMP[lo], RAMP[hi], fStop - lo);
}

function colorizeWordmark(rows, frame) {
  if (!colorEnabled) return rows.slice();
  return rows.map((row, rowIdx) => {
    let out = "";
    for (let col = 0; col < row.length; col++) {
      const ch = row[col];
      if (ch === " ") {
        out += ch;
        continue;
      }
      out += rgb(cellColor(rowIdx, col, row.length, frame)) + ch;
    }
    return out + RESET;
  });
}

// ─────────────────────────── escape-aware width helpers ───────────────────────────

function visibleLength(str) {
  // eslint-disable-next-line no-control-regex
  return str.replace(/\x1b\[[0-9;]*m/g, "").length;
}

function padRight(str, targetVisible) {
  const v = visibleLength(str);
  return v >= targetVisible ? str : str + " ".repeat(targetVisible - v);
}

function padCenter(str, targetVisible) {
  const v = visibleLength(str);
  if (v >= targetVisible) return str;
  const total = targetVisible - v;
  const left = Math.floor(total / 2);
  return " ".repeat(left) + str + " ".repeat(total - left);
}

// ─────────────────────────── box border ───────────────────────────

const TOP_BORDER    = "╭" + "─".repeat(BOX_WIDTH - 2) + "╮";
const BOTTOM_BORDER = "╰" + "─".repeat(BOX_WIDTH - 2) + "╯";
const borderColor = (s) => rgb(PALETTE.violetDeep) + s + RESET;
const row = (content) => borderColor("│") + " " + content + " " + borderColor("│");
const emptyRow = () => row(" ".repeat(INNER_WIDTH));

// ─────────────────────────── subtitle ───────────────────────────

function subtitleRows({ version, calibrationVersion, testCount = 139 }) {
  const dot = graphite("    ·    ");
  const tagline = bold(violet("M A S T E R")) + dot +
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

function composeFrameLines({ wordmarkColored, subtitle }) {
  const lines = [];
  lines.push(borderColor(TOP_BORDER));
  lines.push(emptyRow());

  for (const r of wordmarkColored) {
    lines.push(row(padRight(padCenter(r, INNER_WIDTH), INNER_WIDTH)));
  }
  lines.push(emptyRow());

  for (const s of subtitle) {
    lines.push(row(padRight(padCenter(s, INNER_WIDTH), INNER_WIDTH)));
  }

  lines.push(emptyRow());
  lines.push(borderColor(BOTTOM_BORDER));
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
