/**
 * Animated VelonLabs Banner — Opencode-style wordmark
 * =====================================================
 * No ASCII figure. The brand surface is the wordmark itself, set in
 * 5-row block letters with a vertical violet emboss (lighter top edge,
 * darker bottom edge) and a subtle horizontal sheen that sweeps once
 * on startup before settling. The whole composition is held inside a
 * rounded-corner violet box so the banner reads as a single unit.
 *
 *     ╭───────────────────────────────────────────────────────────────────╮
 *     │                                                                   │
 *     │    █   █  ████  ████  █████  █████  ████                          │  ← brighter (top)
 *     │    ██ ██ ██  ██ ██      █    ██     ██  █                         │
 *     │    █ █ █ █████   ███    █    ████   ████                          │
 *     │    █   █ ██  ██    ██   █    ██     ██  █                         │
 *     │    █   █ ██  ██ ████    █    █████  ██  ██                        │  ← darker (bottom)
 *     │                                                                   │
 *     │    TRADING · SKILLS    ·    by VelonLabs                          │
 *     │    v3.1.0  ·  139 tests  ·  MIT  ·  calibration v2026.05          │
 *     │                                                                   │
 *     ╰───────────────────────────────────────────────────────────────────╯
 *
 * Animation runs only on truecolor TTYs; other terminals get a single
 * static render with the same emboss but no motion.
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

// ─────────────────────────── 5-row block font ───────────────────────────

const FONT = {
  M: ["█   █", "██ ██", "█ █ █", "█   █", "█   █"],
  A: [" ███ ", "█   █", "█████", "█   █", "█   █"],
  S: ["█████", "█    ", "█████", "    █", "█████"],
  T: ["█████", "  █  ", "  █  ", "  █  ", "  █  "],
  E: ["█████", "█    ", "████ ", "█    ", "█████"],
  R: ["████ ", "█   █", "████ ", "█  █ ", "█   █"],
  " ": ["     ", "     ", "     ", "     ", "     "],
};

const WORDMARK_TEXT = "MASTER";
const WORDMARK_GAP = 2; // cols of space between glyphs

function buildWordmark(text) {
  const rows = ["", "", "", "", ""];
  const sep = " ".repeat(WORDMARK_GAP);
  const chars = text.split("");
  chars.forEach((ch, idx) => {
    const glyph = FONT[ch.toUpperCase()] || FONT[" "];
    for (let r = 0; r < 5; r++) {
      rows[r] += glyph[r];
      if (idx < chars.length - 1) rows[r] += sep;
    }
  });
  return rows;
}

const WORDMARK_ROWS = buildWordmark(WORDMARK_TEXT);
const WORDMARK_WIDTH = WORDMARK_ROWS[0].length;
const WORDMARK_HEIGHT = WORDMARK_ROWS.length;

// ─────────────────────────── box dimensions ───────────────────────────

const BOX_WIDTH = 76;                 // total width including borders
const INNER_WIDTH = BOX_WIDTH - 4;    // minus "│ " ... " │"

// ─────────────────────────── color math ───────────────────────────

const lerp = (a, b, t) => a + (b - a) * t;

/** Sample violet ramp at t ∈ [0, 1]. 0 = deep, 1 = soft (light). */
function sampleViolet(t) {
  const a = PALETTE.violetDeep;
  const b = PALETTE.violetSoft;
  return [
    Math.round(lerp(a[0], b[0], t)),
    Math.round(lerp(a[1], b[1], t)),
    Math.round(lerp(a[2], b[2], t)),
  ];
}

/**
 * Render the wordmark with an embossed vertical gradient (lighter at
 * top, darker at bottom) plus an optional horizontal sheen offset by
 * `frame` so a soft highlight slides across the letters.
 */
function colorizeWordmark(rows, frame) {
  if (!colorEnabled) return rows.slice();
  const totalRows = rows.length;
  return rows.map((row, rowIdx) => {
    // Vertical emboss: 1.0 at top → 0.0 at bottom
    const baseT = 1 - rowIdx / (totalRows - 1);
    let out = "";
    for (let col = 0; col < row.length; col++) {
      const ch = row[col];
      if (ch === " ") {
        out += ch;
        continue;
      }
      // Horizontal sheen — gentle sine wave sliding with frame.
      const sheen = Math.sin((col / row.length) * Math.PI * 2 + frame * 0.18) * 0.18;
      const t = Math.max(0, Math.min(1, baseT + sheen));
      out += rgb(sampleViolet(t)) + ch;
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

// ─────────────────────────── frame composition ───────────────────────────

function subtitleRows({ version, calibrationVersion, testCount = 139 }) {
  const dotSep = graphite("  ·  ");
  return [
    [
      bold(violetSoft("TRADING · SKILLS")),
      graphite("by"),
      bold(violet("VelonLabs")),
    ].join("    "),
    [
      `v${version}`,
      `${testCount} tests`,
      `MIT`,
      `calibration v${calibrationVersion}`,
    ].map((s) => violetSoft(s)).join(dotSep),
  ];
}

function composeFrameLines({ wordmarkColored, subtitle }) {
  const lines = [];
  lines.push(borderColor(TOP_BORDER));
  lines.push(emptyRow());

  // Wordmark — centred horizontally inside the box
  for (const r of wordmarkColored) {
    const inner = padRight(padCenter(r, INNER_WIDTH), INNER_WIDTH);
    lines.push(row(inner));
  }

  lines.push(emptyRow());

  // Subtitle block — also centred
  for (const s of subtitle) {
    const inner = padRight(padCenter(s, INNER_WIDTH), INNER_WIDTH);
    lines.push(row(inner));
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
  durationMs = 1500,
  fps = 16,
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

  // First paint
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

  // Settle on canonical frame
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
