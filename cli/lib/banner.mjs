/**
 * Animated VelonLabs Banner
 * ==========================
 * Top of the install ceremony — a framed box with:
 *
 *   ╭──────────────────────────────────────────────────────────────────╮
 *   │                                                                  │
 *   │   [LOGO]      VelonLabs                                          │
 *   │   [LOGO]                                                         │
 *   │   [LOGO]                                                         │
 *   │   [LOGO]                                                         │
 *   │   [LOGO]                                                         │
 *   │                                                                  │
 *   │              ─────────────────────────────                       │
 *   │                                                                  │
 *   │                 master-trading-skills                            │
 *   │      trading skills for autonomous coding agents                 │
 *   │       v3.1.0 · 139 tests · MIT · calibration v2026.05            │
 *   │                                                                  │
 *   ╰──────────────────────────────────────────────────────────────────╯
 *
 * The LOGO cells pulse through the violet brand gradient with a
 * sine-wave phase shift across both axes — the colour appears to roll
 * diagonally, giving a "rotating" feel — and settle to a static frame
 * after ~1.8 s. Border + right-side text stay still throughout.
 *
 * Animation runs only on truecolor TTYs; CI / pipes / no-color
 * terminals fall back to a single static render.
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
// Stylised approximation of the VelonLabs interlocking-hex mark.
// 5 rows × 17 cols (excluding ANSI colour codes). Block elements were
// chosen for stable rendering on Windows Terminal, PowerShell 7,
// macOS Terminal, iTerm2, VS Code, and tmux.
const LOGO_ROWS = [
  "  ▟▀▀▙   ▟▀▀▙  ",
  " ▟█  █▙ ▟█  █▙ ",
  " █   ▜█▟▛   █ ",
  " ▜█  █▟▙█  █▛ ",
  "  ▜▄▄▛   ▜▄▄▛  ",
];

const LOGO_WIDTH = LOGO_ROWS[0].length;
const LOGO_HEIGHT = LOGO_ROWS.length;

const BOX_WIDTH = 76;        // total width including the two border columns
const INNER_WIDTH = BOX_WIDTH - 4; // minus "│ " ... " │"
const LEFT_PAD = 3;          // spaces between border and logo
const LOGO_GAP = 6;          // spaces between logo block and right-side text

// ─────────────────────────── color math ───────────────────────────

function lerp(a, b, t) {
  return a + (b - a) * t;
}

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

/**
 * Apply rotating-gradient phase to logo cells. Each visible cell gets a
 * colour sampled from the violet ramp, indexed by
 *   phase = (col + row*2 + frame*3) mod period
 * pushed through a sine wave for smooth oscillation.
 */
function colorizeLogo(rows, frame) {
  if (!colorEnabled) return rows.slice();
  const period = 28;
  return rows.map((row, rowIdx) => {
    let out = "";
    for (let col = 0; col < row.length; col++) {
      const ch = row[col];
      if (ch === " ") {
        out += ch;
        continue;
      }
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

function borderColor(s) {
  return rgb(PALETTE.violetDeep) + s + RESET;
}

function row(content) {
  // Render one row inside the box. Content must already be padded to INNER_WIDTH.
  return borderColor("│") + " " + content + " " + borderColor("│");
}

function emptyRow() {
  return row(" ".repeat(INNER_WIDTH));
}

// ─────────────────────────── frame composition ───────────────────────────

function rightTextRows({ version, calibrationVersion, testCount = 139 }) {
  const wordmark = bold(violet("VelonLabs"));
  return [
    wordmark,
    "",
    "",
    "",
    "",
  ];
}

function bottomBlockRows({ version, calibrationVersion, testCount = 139 }) {
  const sep = graphite(" · ");
  return [
    graphite("─".repeat(36)),
    "",
    bold(violetSoft("master-trading-skills")),
    graphite("trading skills for autonomous coding agents"),
    [
      `v${version}`,
      `${testCount} tests`,
      `MIT`,
      `calibration v${calibrationVersion}`,
    ].map(violetSoft).join(sep),
  ];
}

function composeFrameLines({ logoColored, rightText, bottomLines }) {
  const lines = [];

  // Top border
  lines.push(borderColor(TOP_BORDER));

  // Top breathing
  lines.push(emptyRow());

  // Logo + right-side wordmark block (5 rows)
  for (let i = 0; i < LOGO_HEIGHT; i++) {
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

  // Spacer
  lines.push(emptyRow());

  // Centered bottom block (divider + product name + tagline + meta)
  for (const ln of bottomLines) {
    const inner = padCenter(ln, INNER_WIDTH);
    lines.push(row(padRight(inner, INNER_WIDTH)));
  }

  // Bottom breathing
  lines.push(emptyRow());

  // Bottom border
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
  durationMs = 1800,
  fps = 18,
} = {}) {
  const rightText = rightTextRows({ version, calibrationVersion, testCount });
  const bottom = bottomBlockRows({ version, calibrationVersion, testCount });

  // No animation: render once, return.
  if (!colorEnabled || !supportsTrueColorOutput || !process.stdout.isTTY) {
    const colored = colorizeLogo(LOGO_ROWS, 0);
    const lines = composeFrameLines({ logoColored: colored, rightText, bottomLines: bottom });
    process.stdout.write(lines.join("\n") + "\n");
    return;
  }

  process.stdout.write(HIDE_CURSOR);

  const totalFrames = Math.max(8, Math.floor((durationMs / 1000) * fps));
  const interval = 1000 / fps;

  // First frame: full paint.
  let lines = composeFrameLines({
    logoColored: colorizeLogo(LOGO_ROWS, 0),
    rightText,
    bottomLines: bottom,
  });
  process.stdout.write(lines.join("\n") + "\n");
  const totalRows = lines.length;

  for (let f = 1; f < totalFrames; f++) {
    await sleep(interval);
    process.stdout.write(moveUp(totalRows) + moveCol1);
    const colored = colorizeLogo(LOGO_ROWS, f);
    lines = composeFrameLines({
      logoColored: colored,
      rightText,
      bottomLines: bottom,
    });
    process.stdout.write(
      lines.map((l) => ERASE_LINE + l).join("\n") + "\n",
    );
  }

  // Settle on canonical resting frame.
  process.stdout.write(moveUp(totalRows) + moveCol1);
  lines = composeFrameLines({
    logoColored: colorizeLogo(LOGO_ROWS, 0),
    rightText,
    bottomLines: bottom,
  });
  process.stdout.write(
    lines.map((l) => ERASE_LINE + l).join("\n") + "\n",
  );

  process.stdout.write(SHOW_CURSOR);
}

/** Static one-shot render (used by tests / non-interactive contexts). */
export function renderBanner(opts = {}) {
  const rightText = rightTextRows(opts);
  const bottom = bottomBlockRows(opts);
  const colored = colorizeLogo(LOGO_ROWS, 0);
  const lines = composeFrameLines({ logoColored: colored, rightText, bottomLines: bottom });
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
    if (sub) {
      for (const line of String(sub).split("\n")) {
        console.log(this.rail("  " + graphite(line)));
      }
    }
  }
  field(key, value) {
    const k = graphite(String(key).padEnd(12, " "));
    console.log(this.rail(`  ${k} ${value}`));
  }
  line(text = "") {
    if (text === "") {
      console.log(this.rail());
    } else {
      for (const l of String(text).split("\n")) {
        console.log(this.rail("  " + l));
      }
    }
  }
  status(label, kind = "done") {
    const map = {
      done: rgb(PALETTE.success) + GLYPHS.check + RESET,
      running: violet("◐"),
      skip: graphite(GLYPHS.dash),
      fail: rgb(PALETTE.danger) + GLYPHS.cross + RESET,
    };
    const icon = map[kind] || map.done;
    console.log(this.rail(`  ${icon} ${label}`));
  }
  tagPill() {
    if (!colorEnabled) {
      console.log(`[${this.tag}]`);
      console.log("");
      return;
    }
    const pill = bgRgb(PALETTE.violet) + " " + bold(`[${this.tag}]`) + " " + RESET;
    console.log(pill);
    console.log("");
  }
  close() {
    console.log(this.rail());
  }
}
