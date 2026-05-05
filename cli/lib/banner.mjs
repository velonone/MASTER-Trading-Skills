/**
 * Banner & Ceremony
 * ==================
 * The startup banner is intentionally large — it sets the tone for the
 * install ceremony that follows. The block-letter title is rendered with
 * a smooth vertical purple gradient, framed by a subtle left rail that
 * connects every step of the install to a single visual spine.
 *
 * Layout reference:
 *
 *   ┌────────────────────────────────────────────────────────────────┐
 *   │                                                                │
 *   │   █▙▖▟█  █▟▖▟█  ████   ████  ████  ████   ████  ████  ████      <─ gradient
 *   │   ▘   ▝  ▘   ▝  ████   ████  ████  ████   ████  ████  ████
 *   │   ████   ████   ████   ████  ████  ████   ████  ████  ████
 *   │                                                                │
 *   │      master-trading-skills                                     │
 *   │      trading skills for autonomous coding agents               │
 *   │      v3.1.0  ·  139 tests  ·  MIT  ·  VelonLabs                │
 *   │                                                                │
 *   └────────────────────────────────────────────────────────────────┘
 *
 *   ┃ [master-trading]
 *   ◆ Source     https://github.com/velonone/MASTER-Trading-Skills
 *   ┃
 *   ◆ Calibration  VelonLabs Reference Snapshot v2026.05
 *   ┃
 *   ◆ Scanning agent runtimes ……
 *   ...
 */

import {
  PALETTE,
  RESET,
  bold,
  dim,
  graphite,
  gradientLines,
  rgb,
  bgRgb,
  violet,
  violetSoft,
  GLYPHS,
  colorEnabled,
} from "./colors.mjs";

// 5×5 block lettering for "MASTER" — a stronger anchor than VELONLABS for
// the product surface. Each character is exactly 5 rows × 5 columns.
const BLOCK = {
  M: ["█   █", "██ ██", "█ █ █", "█   █", "█   █"],
  A: [" ███ ", "█   █", "█████", "█   █", "█   █"],
  S: [" ████", "█    ", " ███ ", "    █", "████ "],
  T: ["█████", "  █  ", "  █  ", "  █  ", "  █  "],
  E: ["█████", "█    ", "████ ", "█    ", "█████"],
  R: ["████ ", "█   █", "████ ", "█  █ ", "█   █"],
  " ": ["     ", "     ", "     ", "     ", "     "],
};

function renderWord(word, gap = 1) {
  const rows = ["", "", "", "", ""];
  const sep = " ".repeat(gap);
  for (let i = 0; i < word.length; i++) {
    const ch = word[i];
    const glyph = BLOCK[ch.toUpperCase()] || BLOCK[" "];
    for (let r = 0; r < 5; r++) {
      rows[r] += glyph[r];
      if (i < word.length - 1) rows[r] += sep;
    }
  }
  return rows;
}

function visibleLength(str) {
  // eslint-disable-next-line no-control-regex
  return str.replace(/\x1b\[[0-9;]*m/g, "").length;
}

/**
 * Render the opening banner. Returns a single string ready to print.
 */
export function renderBanner({
  version,
  calibrationVersion,
  testCount = 139,
} = {}) {
  const lines = [];

  // Block-letter MASTER, vertical purple gradient (deep top → soft bottom)
  const word = renderWord("MASTER", 1);
  const colored = gradientLines(word, PALETTE.violetDeep, PALETTE.violetSoft);

  // The block art is centred in a 64-col canvas
  const canvasWidth = 64;
  const blockVisibleWidth = visibleLength(word[0]);
  const leftPad = Math.max(2, Math.floor((canvasWidth - blockVisibleWidth) / 2));

  lines.push("");
  for (const r of colored) lines.push(" ".repeat(leftPad) + r);

  // Sub-line: TRADING SKILLS in soft violet
  const sub = "TRADING · SKILLS";
  const subPad = Math.max(2, Math.floor((canvasWidth - sub.length) / 2));
  lines.push("");
  lines.push(" ".repeat(subPad) + violetSoft(bold(sub)));

  // Tagline + status
  const tagline = graphite("trading skills for autonomous coding agents");
  const taglinePad = Math.max(2, Math.floor((canvasWidth - visibleLength(tagline)) / 2));
  lines.push("");
  lines.push(" ".repeat(taglinePad) + tagline);

  const status = [
    `v${version || "?"}`,
    `${testCount} tests`,
    `MIT`,
    `calibration ${calibrationVersion || "?"}`,
    `VelonLabs`,
  ].map(violetSoft).join(graphite(" · "));
  const statusPad = Math.max(2, Math.floor((canvasWidth - visibleLength(status)) / 2));
  lines.push(" ".repeat(statusPad) + status);

  lines.push("");
  return lines.join("\n");
}

// ─────────────────────────── Ceremony rail ───────────────────────────

/**
 * State held while we're emitting a ceremony — the left rail tracks the
 * visual spine that connects banner → step 1 → step 2 → … → done.
 */
export class Ceremony {
  constructor(tag = "master-trading") {
    this.tag = tag;
    this._opened = false;
  }

  rail(extra = "") {
    return graphite(GLYPHS.treeVert) + (extra ? "  " + extra : "");
  }

  /** Print a section header with a violet diamond marker. */
  section(label, sub = "") {
    if (this._opened) console.log(this.rail());
    this._opened = true;
    const head = violet(GLYPHS.diamond) + "  " + bold(label);
    console.log(head);
    if (sub) {
      for (const line of String(sub).split("\n")) {
        console.log(this.rail("  " + graphite(line)));
      }
    }
  }

  /** Print a `key: value` line under the current section. */
  field(key, value) {
    const k = graphite(String(key).padEnd(12, " "));
    console.log(this.rail(`  ${k} ${value}`));
  }

  /** Plain rail-aligned text. */
  line(text = "") {
    if (text === "") {
      console.log(this.rail());
    } else {
      for (const l of String(text).split("\n")) {
        console.log(this.rail("  " + l));
      }
    }
  }

  /** Status sub-step (·  done / running / fail). */
  status(label, kind = "done") {
    const map = {
      done:    rgb(PALETTE.success) + GLYPHS.check + RESET,
      running: violet("◐"),
      skip:    graphite(GLYPHS.dash),
      fail:    rgb(PALETTE.danger) + GLYPHS.cross + RESET,
    };
    const icon = map[kind] || map.done;
    console.log(this.rail(`  ${icon} ${label}`));
  }

  /** Render the project tag once at the top (cyan-on-dark pill). */
  tagPill() {
    if (!colorEnabled) {
      console.log(`[${this.tag}]`);
      console.log("");
      return;
    }
    const pill =
      bgRgb(PALETTE.violet) + " " + bold(`[${this.tag}]`) + " " + RESET;
    console.log(pill);
    console.log("");
  }

  /** Soft divider used at the very end. */
  close() {
    console.log(this.rail());
  }
}
