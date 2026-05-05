/**
 * VelonLabs Banner — static block-letter wordmark
 * ====================================================
 * Compact rewrite: no animation, no frame cycling, no ridges. The
 * wordmark renders as 5-row block letters with a 5-stop vertical
 * violet gradient (highlight at the top edge, shadow at the
 * baseline). Smaller than the previous 6-row 2-col-stroke build by
 * roughly 30 % in both axes — fits comfortably above the install
 * ceremony without dominating the first screen.
 *
 *     V E L O N L A B S
 *     █   █ █████ █     █████ █   █ █     █████ █████ █████   ← #E8DCFF
 *     █   █ █     █     █   █ ██  █ █     █   █ █   █ █          #B5A3FF
 *     █   █ ███   █     █   █ █ █ █ █     █████ ████  ████       #7C5CFF (brand)
 *      █ █  █     █     █   █ █  ██ █     █   █ █   █     █      #5840D4
 *       █   █████ █████ █████ █   █ █████ █   █ █████ █████   ← #3A2A8F
 *
 *     M A S T E R    ·    T R A D I N G    ·    S K I L L S
 *     v3.1.0 · 139 tests · MIT · calibration v2026.05
 *
 * The frame data in cli/lib/banner-frames.mjs is preserved for
 * possible future reuse but is no longer imported here.
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
} from "./colors.mjs";

// ─────────────────────────── 5×5 block font ───────────────────────────
//
// 1-col strokes, 1-col gap between glyphs. Case-sensitive lookup so we
// could expand to mixed case later — for now everything in WORDMARK_TEXT
// is uppercase.

const FONT = {
  V: [
    "█   █",
    "█   █",
    "█   █",
    " █ █ ",
    "  █  ",
  ],
  E: [
    "█████",
    "█    ",
    "███  ",
    "█    ",
    "█████",
  ],
  L: [
    "█    ",
    "█    ",
    "█    ",
    "█    ",
    "█████",
  ],
  O: [
    "█████",
    "█   █",
    "█   █",
    "█   █",
    "█████",
  ],
  N: [
    "█   █",
    "██  █",
    "█ █ █",
    "█  ██",
    "█   █",
  ],
  A: [
    " ███ ",
    "█   █",
    "█████",
    "█   █",
    "█   █",
  ],
  B: [
    "████ ",
    "█   █",
    "████ ",
    "█   █",
    "████ ",
  ],
  S: [
    "█████",
    "█    ",
    "█████",
    "    █",
    "█████",
  ],
  " ": [
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
  ],
};

const WORDMARK_TEXT = "VELONLABS";
const WORDMARK_GAP = 1;

function buildWordmark(text) {
  const rows = ["", "", "", "", ""];
  const sep = " ".repeat(WORDMARK_GAP);
  const chars = text.split("");
  chars.forEach((ch, idx) => {
    const glyph = FONT[ch] || FONT[" "];
    for (let r = 0; r < 5; r++) {
      rows[r] += glyph[r];
      if (idx < chars.length - 1) rows[r] += sep;
    }
  });
  return rows;
}

const WORDMARK_ROWS = buildWordmark(WORDMARK_TEXT);

// ─────────────────────────── 5-stop violet ramp ───────────────────────────

const RAMP = [
  [232, 220, 255], // 0 — highlight (cap-top edge)
  [181, 163, 255], // 1
  [124,  92, 255], // 2 — brand violet
  [ 88,  64, 212], // 3
  [ 58,  42, 143], // 4 — shadow (baseline)
];

function colorizeWordmark(rows) {
  if (!colorEnabled) return rows.slice();
  return rows.map((row, rowIdx) => {
    let out = "";
    for (let col = 0; col < row.length; col++) {
      const ch = row[col];
      if (ch === " ") { out += ch; continue; }
      out += rgb(RAMP[rowIdx]) + ch + RESET;
    }
    return out;
  });
}

// ─────────────────────────── subtitle ───────────────────────────

function subtitleLines({ version, calibrationVersion, testCount = 139 }) {
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

// ─────────────────────────── compose ───────────────────────────

const INDENT = "    ";

function composeLines({ version, calibrationVersion, testCount }) {
  const wordmark = colorizeWordmark(WORDMARK_ROWS);
  const subtitle = subtitleLines({ version, calibrationVersion, testCount });
  const lines = [""];
  for (const r of wordmark) lines.push(INDENT + r);
  lines.push("");
  for (const s of subtitle) lines.push(INDENT + s);
  lines.push("");
  return lines;
}

// ─────────────────────────── public API ───────────────────────────

/**
 * Render the banner once (no animation) and return immediately.
 * Kept async-compatible so existing callers that `await` it still work.
 */
export async function animateBanner(opts = {}) {
  const lines = composeLines({
    version: opts.version || "?",
    calibrationVersion: opts.calibrationVersion || "?",
    testCount: opts.testCount || 139,
  });
  process.stdout.write(lines.join("\n") + "\n");
}

export function renderBanner(opts = {}) {
  const lines = composeLines({
    version: opts.version || "?",
    calibrationVersion: opts.calibrationVersion || "?",
    testCount: opts.testCount || 139,
  });
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
