/**
 * VelonLabs Banner — pre-rendered animation + 3D ridges
 * =======================================================
 * Runs the user-designed 30-frame VELONLABS animation (each frame is
 * a multi-line ANSI string built from `▓`/`░` cells with truecolor
 * escapes) and frames it with two extra layers for depth:
 *
 *   ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔  ← highlight ridge (cap-top)
 *   [animated VELONLABS frames cycle here]
 *   ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁  ← shadow ridge (baseline)
 *
 *   M A S T E R  ·  T R A D I N G  ·  S K I L L S
 *   v3.1.0 · 139 tests · MIT · calibration v2026.05
 *
 * The two ridges read as a "raised plate" the wordmark sits on — bright
 * on top (light from above), dark on bottom (cast shadow). Combined with
 * the per-frame colour cycling inside the wordmark, the whole banner
 * has a clear 3D feel without needing actual perspective rendering.
 *
 * Animation runs only on truecolor TTYs; no-color terminals get a
 * single static render of frame 0 with the ridges flattened to grey.
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
import { FRAMES as RAW_FRAMES, NATIVE_FPS } from "./banner-frames.mjs";

// ─────────────────────────── frame preprocessing ───────────────────────────
//
// Each raw frame ends with two source-design footer lines we don't want
// (the original was a "design system framework" wordmark). Strip them
// so we only keep the wordmark rows; banner.mjs supplies its own
// subtitle below.

function cleanFrame(frame) {
  // 1. Strip the source design's footer text (everything after the first
  //    blank line) so we keep only the 10-row wordmark.
  // 2. Replace every "░" with a plain space. In the source data those
  //    light-shade glyphs appear without colour escapes — they render
  //    as default-foreground grey haze around the letters and read as
  //    noise. Spaces let the coloured "▓" cells float on a clean
  //    background so the letterforms actually pop.
  const lines = frame.split("\n");
  const idx = lines.findIndex((l) => l.trim() === "");
  const wordmarkOnly = idx > 0 ? lines.slice(0, idx) : lines;
  return wordmarkOnly.map((line) => line.replace(/░/g, " ")).join("\n");
}

const FRAMES = RAW_FRAMES.map(cleanFrame);
const WORDMARK_LINE_COUNT = FRAMES[0].split("\n").length;

// Compute the visible width of the wordmark (after stripping ANSI).
function visibleLength(str) {
  // eslint-disable-next-line no-control-regex
  return str.replace(/\x1b\[[0-9;]*m/g, "").length;
}

const WORDMARK_WIDTH = Math.max(
  ...FRAMES[0].split("\n").map((l) => visibleLength(l)),
);

// ─────────────────────────── 3D ridges ───────────────────────────

const RIDGE_HIGHLIGHT = [232, 220, 255]; // cap-top edge highlight
const RIDGE_SHADOW    = [ 32, 18,  68]; // base shadow (almost black)

function ridgeLine(charSet, color) {
  if (!colorEnabled) return charSet.repeat(WORDMARK_WIDTH);
  return rgb(color) + charSet.repeat(WORDMARK_WIDTH) + RESET;
}

const HIGHLIGHT_RIDGE = () => ridgeLine("▔", RIDGE_HIGHLIGHT);
const SHADOW_RIDGE    = () => ridgeLine("▁", RIDGE_SHADOW);

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

// ─────────────────────────── compose a printable frame ───────────────────────────

const INDENT = "    ";

function composeBlock({ wordmark, subtitle }) {
  const lines = [];
  lines.push("");
  lines.push(INDENT + HIGHLIGHT_RIDGE());

  for (const wm of wordmark.split("\n")) {
    lines.push(INDENT + wm);
  }

  lines.push(INDENT + SHADOW_RIDGE());
  lines.push("");
  for (const s of subtitle) lines.push(INDENT + s);
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
  cycles = 3,                    // ~3.75 s of animation at 24 fps
  fps = NATIVE_FPS,
} = {}) {
  const subtitle = subtitleLines({ version, calibrationVersion, testCount });

  // Static path: render last frame once and return.
  if (!colorEnabled || !supportsTrueColorOutput || !process.stdout.isTTY) {
    const lines = composeBlock({
      wordmark: FRAMES[FRAMES.length - 1],
      subtitle,
    });
    process.stdout.write(lines.join("\n") + "\n");
    return;
  }

  process.stdout.write(HIDE_CURSOR);

  // Initial paint
  let lines = composeBlock({ wordmark: FRAMES[0], subtitle });
  process.stdout.write(lines.join("\n") + "\n");
  const totalRows = lines.length;

  const interval = 1000 / fps;
  const totalFrames = FRAMES.length * Math.max(1, cycles);

  for (let f = 1; f < totalFrames; f++) {
    await sleep(interval);
    process.stdout.write(moveUp(totalRows) + moveCol1);
    lines = composeBlock({
      wordmark: FRAMES[f % FRAMES.length],
      subtitle,
    });
    process.stdout.write(lines.map((l) => ERASE_LINE + l).join("\n") + "\n");
  }

  process.stdout.write(SHOW_CURSOR);
}

export function renderBanner(opts = {}) {
  const subtitle = subtitleLines({
    version: opts.version || "?",
    calibrationVersion: opts.calibrationVersion || "?",
    testCount: opts.testCount || 139,
  });
  const lines = composeBlock({
    wordmark: FRAMES[FRAMES.length - 1],
    subtitle,
  });
  return lines.join("\n");
}

// ─────────────────────────── ceremony rail (unchanged) ───────────────────────────

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
