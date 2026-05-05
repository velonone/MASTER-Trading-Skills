/**
 * Build the GitHub Social Preview card.
 *
 *     1280 × 640 px · violet brand background · typographic-first design
 *
 * Outputs two files into docs/assets/brand/:
 *   - velonlabs-social-card.svg  (editable source, ~5 KB)
 *   - velonlabs-social-card.png  (uploaded to GitHub Settings, < 1 MB)
 *
 * Run:
 *   node tools/build-social-card.mjs
 *
 * Requires sharp for the SVG → PNG step (auto-installed at ~/.npm cache).
 */

import { writeFileSync } from "fs";
import { resolve } from "path";
import { fileURLToPath } from "url";
import { dirname } from "path";
import sharp from "sharp";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const REPO_ROOT = resolve(__dirname, "..");
const OUT_DIR = resolve(REPO_ROOT, "docs", "assets", "brand");

const W = 1280;
const H = 640;

// Brand palette
const VIOLET = "#7C5CFF";
const VIOLET_SOFT = "#B5A3FF";
const VIOLET_DEEP = "#5840D4";
const INK = "#0A0414";
const PAPER = "#FAFAFC";

// ─────────────────────────── SVG composition ───────────────────────────

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <defs>
    <!-- Diagonal background gradient: deep ink → violet → ink -->
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"   stop-color="${INK}"/>
      <stop offset="55%"  stop-color="#1A0F3A"/>
      <stop offset="100%" stop-color="${INK}"/>
    </linearGradient>

    <!-- Soft radial glow behind the V monogram -->
    <radialGradient id="glow" cx="0.22" cy="0.5" r="0.4" fx="0.22" fy="0.5">
      <stop offset="0%"   stop-color="${VIOLET}" stop-opacity="0.35"/>
      <stop offset="60%"  stop-color="${VIOLET}" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="${VIOLET}" stop-opacity="0"/>
    </radialGradient>

    <!-- Title gradient: white at top → violetSoft at bottom -->
    <linearGradient id="title" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="${PAPER}"/>
      <stop offset="100%" stop-color="${VIOLET_SOFT}"/>
    </linearGradient>

    <!-- Subtle vertical fade for the V strokes -->
    <linearGradient id="vstroke" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="${VIOLET_SOFT}"/>
      <stop offset="100%" stop-color="${VIOLET_DEEP}"/>
    </linearGradient>
  </defs>

  <!-- Layered background -->
  <rect width="${W}" height="${H}" fill="url(#bg)"/>
  <rect width="${W}" height="${H}" fill="url(#glow)"/>

  <!-- Subtle grid lines for technical feel -->
  <g stroke="${VIOLET}" stroke-width="0.5" opacity="0.06">
    <line x1="0"    y1="160" x2="${W}" y2="160"/>
    <line x1="0"    y1="320" x2="${W}" y2="320"/>
    <line x1="0"    y1="480" x2="${W}" y2="480"/>
    <line x1="320"  y1="0"   x2="320"  y2="${H}"/>
    <line x1="640"  y1="0"   x2="640"  y2="${H}"/>
    <line x1="960"  y1="0"   x2="960"  y2="${H}"/>
  </g>

  <!-- ───── LEFT: V monogram ───── -->
  <g transform="translate(140, 180)">
    <!-- Outer V outline -->
    <path
      d="M 20 20 L 140 260 L 260 20"
      fill="none"
      stroke="url(#vstroke)"
      stroke-width="22"
      stroke-linejoin="miter"
      stroke-linecap="square"/>
    <!-- Inner accent V (offset, lighter) -->
    <path
      d="M 70 40 L 140 200 L 210 40"
      fill="none"
      stroke="${VIOLET_SOFT}"
      stroke-width="14"
      stroke-linejoin="miter"
      stroke-linecap="square"
      opacity="0.55"/>
  </g>

  <!-- ───── RIGHT: text block ───── -->
  <g font-family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif">
    <!-- Brand pill -->
    <g transform="translate(480, 188)">
      <rect width="160" height="34" rx="17"
        fill="${VIOLET}" fill-opacity="0.15"
        stroke="${VIOLET}" stroke-width="1.2"/>
      <text x="80" y="23"
        font-size="13" font-weight="600"
        fill="${VIOLET_SOFT}" text-anchor="middle"
        letter-spacing="3.5">VELONLABS</text>
    </g>

    <!-- Main title -->
    <text x="480" y="310"
      font-size="62" font-weight="800"
      fill="url(#title)">master-trading-skills</text>

    <!-- Tagline (two lines) -->
    <text x="480" y="375"
      font-size="26" font-weight="400"
      fill="${VIOLET_SOFT}" opacity="0.85">Trading infrastructure your AI agent</text>
    <text x="480" y="412"
      font-size="26" font-weight="400"
      fill="${VIOLET_SOFT}" opacity="0.85">can actually audit.</text>

    <!-- Status row -->
    <text x="480" y="490"
      font-size="18" font-weight="500"
      font-family="JetBrains Mono, ui-monospace, Menlo, monospace"
      fill="${VIOLET}" letter-spacing="1.2">v3.1.0   ·   139 tests   ·   MIT   ·   by VelonLabs</text>
  </g>

  <!-- Bottom accent rule -->
  <rect x="0" y="${H - 4}" width="${W}" height="4"
    fill="${VIOLET}" opacity="0.75"/>
</svg>`;

// ─────────────────────────── write SVG ───────────────────────────

const svgPath = resolve(OUT_DIR, "velonlabs-social-card.svg");
writeFileSync(svgPath, svg);
console.log(`✓ SVG  ${svgPath}  (${svg.length} bytes)`);

// ─────────────────────────── render PNG ───────────────────────────

const pngPath = resolve(OUT_DIR, "velonlabs-social-card.png");
const pngBuffer = await sharp(Buffer.from(svg), { density: 144 })
  .resize(W, H, { fit: "fill" })
  .png({ compressionLevel: 9 })
  .toBuffer();
writeFileSync(pngPath, pngBuffer);
console.log(`✓ PNG  ${pngPath}  (${pngBuffer.length} bytes)`);
