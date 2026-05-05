/**
 * ANSI Color Helpers — VelonLabs Brand Palette
 * =============================================
 * Pure-Node 24-bit (truecolor) ANSI escapes with graceful 256-color and
 * no-color fallbacks. Designed to render correctly in:
 *
 *   • Windows Terminal (truecolor)
 *   • PowerShell 7+   (truecolor)
 *   • macOS Terminal  (truecolor)
 *   • iTerm2          (truecolor)
 *   • Old cmd.exe     (degrades to 256-color)
 *   • CI / non-tty    (no color)
 */

const env = process.env;
const isTTY = process.stdout.isTTY;

// Heuristic — modern terminals advertise truecolor.
const supportsTrueColor =
  isTTY &&
  !env.NO_COLOR &&
  (env.COLORTERM === "truecolor" ||
    env.COLORTERM === "24bit" ||
    env.TERM_PROGRAM === "vscode" ||
    env.TERM_PROGRAM === "WindowsTerminal" ||
    env.WT_SESSION ||
    env.TERM === "xterm-256color" ||
    env.TERM === "xterm-kitty" ||
    process.platform === "win32"); // PowerShell 7+ defaults to truecolor

const supportsColor = isTTY && !env.NO_COLOR;

// VelonLabs brand palette (RGB triples).
export const PALETTE = {
  violet:       [124, 92, 255],   // #7C5CFF — primary
  violetDeep:   [88, 64, 212],    // #5840D4
  violetSoft:   [181, 163, 255],  // #B5A3FF
  ink:          [10, 10, 20],     // #0A0A14
  paper:        [250, 250, 252],  // #FAFAFC
  graphite:     [82, 82, 107],    // #52526B
  success:      [40, 199, 111],   // #28C76F
  warning:      [255, 181, 71],   // #FFB547
  danger:       [255, 77, 109],   // #FF4D6D
  muted:        [120, 120, 140],
};

// ─────────────────────────── core escape sequences ───────────────────────────

const ESC = "\x1b[";
export const RESET = supportsColor ? ESC + "0m" : "";
export const BOLD = supportsColor ? ESC + "1m" : "";
export const DIM = supportsColor ? ESC + "2m" : "";
export const ITALIC = supportsColor ? ESC + "3m" : "";
export const UNDERLINE = supportsColor ? ESC + "4m" : "";

/**
 * Render foreground color from an [r, g, b] triple. Falls back to a
 * 256-color approximation, then to no color.
 */
export function rgb([r, g, b]) {
  if (!supportsColor) return "";
  if (supportsTrueColor) return `${ESC}38;2;${r};${g};${b}m`;
  // 6×6×6 cube approximation
  const idx = 16 +
    36 * Math.round((r / 255) * 5) +
    6 * Math.round((g / 255) * 5) +
    Math.round((b / 255) * 5);
  return `${ESC}38;5;${idx}m`;
}

/** Background variant. */
export function bgRgb([r, g, b]) {
  if (!supportsColor) return "";
  if (supportsTrueColor) return `${ESC}48;2;${r};${g};${b}m`;
  const idx = 16 +
    36 * Math.round((r / 255) * 5) +
    6 * Math.round((g / 255) * 5) +
    Math.round((b / 255) * 5);
  return `${ESC}48;5;${idx}m`;
}

// ─────────────────────────── named helpers ───────────────────────────

export const violet     = (s) => `${rgb(PALETTE.violet)}${s}${RESET}`;
export const violetSoft = (s) => `${rgb(PALETTE.violetSoft)}${s}${RESET}`;
export const violetDeep = (s) => `${rgb(PALETTE.violetDeep)}${s}${RESET}`;
export const graphite   = (s) => `${rgb(PALETTE.graphite)}${s}${RESET}`;
export const muted      = (s) => `${rgb(PALETTE.muted)}${s}${RESET}`;
export const success    = (s) => `${rgb(PALETTE.success)}${s}${RESET}`;
export const warning    = (s) => `${rgb(PALETTE.warning)}${s}${RESET}`;
export const danger     = (s) => `${rgb(PALETTE.danger)}${s}${RESET}`;
export const bold       = (s) => `${BOLD}${s}${RESET}`;
export const dim        = (s) => `${DIM}${s}${RESET}`;
export const italic     = (s) => `${ITALIC}${s}${RESET}`;

// ─────────────────────────── gradient ───────────────────────────

/**
 * Render `text` with a smooth color gradient between two RGB endpoints.
 * Whitespace is left uncoloured so the escape sequences stay tight.
 */
export function gradient(text, fromRgb, toRgb) {
  if (!supportsColor) return text;
  const visible = [...text].filter((c) => c !== " " && c !== "\n").length;
  if (visible <= 1) return rgb(fromRgb) + text + RESET;

  let out = "";
  let i = 0;
  for (const ch of text) {
    if (ch === " " || ch === "\n") {
      out += ch;
      continue;
    }
    const t = i / (visible - 1);
    const r = Math.round(fromRgb[0] + (toRgb[0] - fromRgb[0]) * t);
    const g = Math.round(fromRgb[1] + (toRgb[1] - fromRgb[1]) * t);
    const b = Math.round(fromRgb[2] + (toRgb[2] - fromRgb[2]) * t);
    out += rgb([r, g, b]) + ch;
    i++;
  }
  return out + RESET;
}

/** Vertical gradient for multi-line ASCII art — colours each line uniformly. */
export function gradientLines(lines, fromRgb, toRgb) {
  if (!supportsColor) return lines;
  if (lines.length <= 1) return lines.map((l) => rgb(fromRgb) + l + RESET);
  return lines.map((line, i) => {
    const t = i / (lines.length - 1);
    const r = Math.round(fromRgb[0] + (toRgb[0] - fromRgb[0]) * t);
    const g = Math.round(fromRgb[1] + (toRgb[1] - fromRgb[1]) * t);
    const b = Math.round(fromRgb[2] + (toRgb[2] - fromRgb[2]) * t);
    return rgb([r, g, b]) + line + RESET;
  });
}

// ─────────────────────────── glyphs ───────────────────────────

export const GLYPHS = {
  diamond:    "◆",
  diamondOpen:"◇",
  circle:     "●",
  circleOpen: "◯",
  check:      "✓",
  cross:      "✗",
  dash:       "─",
  arrowRight: "→",
  bullet:     "•",
  spinner:    ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
  treeBranch: "├─",
  treeLast:   "└─",
  treeVert:   "│",
};

export const supportsTrueColorOutput = supportsTrueColor;
export const colorEnabled = supportsColor;
