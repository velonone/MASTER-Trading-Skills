/**
 * Animated VelonLabs Banner — compact framed layout
 * ===================================================
 * The mark on the left is a stylised "V" letter (VelonLabs's V) drawn
 * with diagonal block strokes — clean enough to read as a glyph in any
 * terminal, sharp enough to feel like a brand mark. It pulses through
 * the brand violet ramp with a sine-wave phase shift so the colour
 * appears to rotate; the right-side text and the box border stay still.
 *
 * Layout (76 cols wide, 8 rows tall including borders):
 *
 *   ╭────────────────────────────────────────────────────────────────────────╮
 *   │                                                                        │
 *   │   █▙       ▟█      VelonLabs                                           │
 *   │    █▙     ▟█       master-trading-skills · v3.1.0                      │
 *   │     █▙   ▟█        trading skills for autonomous coding agents         │
 *   │      ▜█▙▟█▛        139 tests · MIT · calibration v2026.05              │
 *   │                                                                        │
 *   ╰────────────────────────────────────────────────────────────────────────╯
 *
 * The V is 4 rows × 11 cols. Right-side text is 4 rows packed tight.
 * Animation runs only on truecolor TTYs; non-TTY / no-color terminals
 * get a single static render.
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

// ─────────────────────────── ASCII logo ───────────────────────────
//
// Diagonal V drawn with block elements. Each row is 11 cols wide.
// The strokes are 2 cols thick so the V reads at a glance.
const LOGO_ROWS = [
  "█▙       ▟█",
  " █▙     ▟█ ",
  "  █▙   ▟█  ",
  "   ▜█▙▟█▛  ",
];

const LOGO_WIDTH = LOGO_ROWS[0].length;
const LOGO_HEIGHT = LOGO_ROWS.length;

const BOX_WIDTH = 76;                 // total width including border columns
const INNER_WIDTH = BOX_WIDTH - 4;    // minus "│ " ... " │"
const LEFT_PAD = 3;                   // space between border and logo
const LOGO_GAP = 6;                   // space between logo and right-side text

// ─────────────────────────── color math ───────────────────────────

const lerp = (a, b, t) => a + (b - a) * t;

/** Sample violet ramp at t∈[0,1] (0=deep, 1=soft). */
function sampleViolet(t) {
  const a = PALETTE.violetDeep;
  const b = PALETTE.violetSoft;
  return [
    Math.round(lerp(a[0], b[0], t)),
    Math.round(lerp(a[1], b[1], t)),
    Math.round(lerp(a[2], b[2], t)),
  ];
}

/** Apply rotating-gradient phase to the V cells. */
function colorizeLogo(rows, frame) {
  if (!colorEnabled) return rows.slice();
  const period = 24;
  return rows.map((row, rowIdx) => {
    let out = "";
    for (let col = 0; col < row.length; col++) {
      const ch = row[col];
      if (ch === " ") {
        out += ch;
        continue;
      }
      // Phase shifts diagonally: col + 2*row + 3*frame.
      const phase = (col + rowIdx * 2 + frame * 3) % period;
      const t = (1 + Math.sin((phase / period) * Math.PI * 2)) / 2;
      out += rgb(sampleViolet(t)) + ch;
    }
    return out + RESET;
  });
}

// ─────────────────────────── escape-aware width ───────────────────────────

function visibleLength(str) {
  // eslint-disable-next-line no-control-regex
  return str.replace(/\x1b\[[0-9;]*m/g, "").length;
}

function padRight(str, targetVisible) {
  const v = visibleLength(str);
  return v >= targetVisible ? str : str + " ".repeat(targetVisible - v);
}

// ─────────────────────────── box border ───────────────────────────

const TOP_BORDER    = "╭" + "─".repeat(BOX_WIDTH - 2) + "╮";
const BOTTOM_BORDER = "╰" + "─".repeat(BOX_WIDTH - 2) + "╯";

const borderColor = (s) => rgb(PALETTE.violetDeep) + s + RESET;

function row(content) {
  return borderColor("│") + " " + content + " " + borderColor("│");
}

const emptyRow = () => row(" ".repeat(INNER_WIDTH));

// ─────────────────────────── right-side text ───────────────────────────

function rightTextRows({ version, calibrationVersion, testCount = 139 }) {
  const sep = graphite(" · ");
  return [
    bold(violet("VelonLabs")),
    bold(violetSoft("master-trading-skills")) + dim(" · v" + version),
    graphite("trading skills for autonomous coding agents"),
    [
      `${testCount} tests`,
      `MIT`,
      `calibration v${calibrationVersion}`,
    ].map(violetSoft).join(sep),
  ];
}

// ─────────────────────────── frame composition ───────────────────────────

function composeFrameLines({ logoColored, rightText }) {
  const lines = [];
  lines.push(borderColor(TOP_BORDER));
  lines.push(emptyRow());

  // Content rows — height = max(logo, right text). For our spec both are 4.
  const contentHeight = Math.max(logoColored.length, rightText.length);
  for (let i = 0; i < contentHeight; i++) {
    const logo = i < logoColored.length ? logoColored[i] : " ".repeat(LOGO_WIDTH);
    const text = i < rightText.length ? rightText[i] : "";
    let inner =
      " ".repeat(LEFT_PAD) +
      padRight(logo, LOGO_WIDTH) +
      " ".repeat(LOGO_GAP) +
      text;
    inner = padRight(inner, INNER_WIDTH);
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
  durationMs = 1600,
  fps = 18,
} = {}) {
  const rightText = rightTextRows({ version, calibrationVersion, testCount });

  if (!colorEnabled || !supportsTrueColorOutput || !process.stdout.isTTY) {
    const colored = colorizeLogo(LOGO_ROWS, 0);
    const lines = composeFrameLines({ logoColored: colored, rightText });
    process.stdout.write(lines.join("\n") + "\n");
    return;
  }

  process.stdout.write(HIDE_CURSOR);

  const totalFrames = Math.max(8, Math.floor((durationMs / 1000) * fps));
  const interval = 1000 / fps;

  // First paint
  let lines = composeFrameLines({
    logoColored: colorizeLogo(LOGO_ROWS, 0),
    rightText,
  });
  process.stdout.write(lines.join("\n") + "\n");
  const totalRows = lines.length;

  for (let f = 1; f < totalFrames; f++) {
    await sleep(interval);
    process.stdout.write(moveUp(totalRows) + moveCol1);
    lines = composeFrameLines({
      logoColored: colorizeLogo(LOGO_ROWS, f),
      rightText,
    });
    process.stdout.write(lines.map((l) => ERASE_LINE + l).join("\n") + "\n");
  }

  // Settle on canonical frame.
  process.stdout.write(moveUp(totalRows) + moveCol1);
  lines = composeFrameLines({
    logoColored: colorizeLogo(LOGO_ROWS, 0),
    rightText,
  });
  process.stdout.write(lines.map((l) => ERASE_LINE + l).join("\n") + "\n");

  process.stdout.write(SHOW_CURSOR);
}

export function renderBanner(opts = {}) {
  const rightText = rightTextRows({
    version: opts.version || "?",
    calibrationVersion: opts.calibrationVersion || "?",
    testCount: opts.testCount || 139,
  });
  const colored = colorizeLogo(LOGO_ROWS, 0);
  const lines = composeFrameLines({ logoColored: colored, rightText });
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
