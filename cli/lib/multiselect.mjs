/**
 * Interactive Arrow-Key Multi-Select
 * ====================================
 * Pure-Node implementation (no deps) using raw TTY mode + ANSI cursor
 * positioning. Up/Down to navigate, Space to toggle, A to toggle all,
 * Enter to confirm, Esc / Ctrl-C to cancel.
 *
 * Items can declare:
 *   { value, label, description?, required?, hint?, group? }
 *
 * Required items are pre-selected and cannot be unchecked.
 */

import {
  PALETTE,
  RESET,
  bold,
  dim,
  graphite,
  muted,
  rgb,
  violet,
  violetSoft,
  GLYPHS,
  colorEnabled,
} from "./colors.mjs";

const stdin = process.stdin;
const stdout = process.stdout;

// ANSI helpers
const HIDE_CURSOR = colorEnabled ? "\x1b[?25l" : "";
const SHOW_CURSOR = colorEnabled ? "\x1b[?25h" : "";
const CLEAR_LINE = colorEnabled ? "\x1b[2K" : "";
const ERASE_DOWN = colorEnabled ? "\x1b[J" : "";
const moveUp = (n) => (n > 0 && colorEnabled ? `\x1b[${n}A` : "");
const moveCol1 = colorEnabled ? "\x1b[G" : "";

function visibleLength(str) {
  // eslint-disable-next-line no-control-regex
  return str.replace(/\x1b\[[0-9;]*m/g, "").length;
}

function rail(extra = "") {
  return graphite(GLYPHS.treeVert) + (extra ? "  " + extra : "");
}

function renderItem(item, isCursor, isSelected) {
  const cursorMark = isCursor ? violet("❯") : " ";
  const checkbox = item.required
    ? rgb(PALETTE.success) + "■" + RESET
    : isSelected
      ? rgb(PALETTE.success) + "■" + RESET
      : graphite("□");
  const labelColor = isCursor ? bold(violetSoft(item.label)) : item.label;
  const required = item.required ? " " + graphite("[required]") : "";
  const main = `${cursorMark} ${checkbox} ${labelColor}${required}`;
  return main;
}

function renderDescription(item, isCursor) {
  if (!item.description) return null;
  const colour = isCursor ? graphite : muted;
  return `      ${colour(item.description)}`;
}

/**
 * Run the multi-select.
 *
 * @param {object} opts
 * @param {string} opts.title             Header line printed once.
 * @param {string} [opts.subtitle]        Optional second line.
 * @param {Array}  opts.items             Items to choose from.
 * @param {Set}    [opts.preSelected]     Set of values starting selected.
 * @returns {Promise<string[]>}           Selected values in declaration order.
 */
export async function multiSelect({
  title,
  subtitle,
  items,
  preSelected,
} = {}) {
  if (!stdin.isTTY) {
    // Fallback: select required + first non-required for non-interactive.
    return items
      .filter((i) => i.required || preSelected?.has(i.value))
      .map((i) => i.value);
  }

  const selected = new Set();
  for (const it of items) {
    if (it.required) selected.add(it.value);
    if (preSelected && preSelected.has(it.value)) selected.add(it.value);
  }
  let cursor = 0;
  let cancelled = false;
  let confirmed = false;

  // We need to know how many lines we drew so we can erase them between
  // re-renders. Each item is 1 line of header + optional 1 line of description.
  let lastRenderedLines = 0;

  function buildView() {
    const lines = [];
    lines.push(rail());
    lines.push(violet(GLYPHS.diamond) + "  " + bold(title));
    if (subtitle) {
      lines.push(rail("  " + graphite(subtitle)));
    }
    const hint = graphite(
      "↑↓ navigate · space toggle · a toggle-all · enter confirm · esc cancel",
    );
    lines.push(rail("  " + hint));
    lines.push(rail());

    let prevGroup = null;
    items.forEach((item, idx) => {
      const isCursor = idx === cursor;
      const isSelected = selected.has(item.value);

      if (item.group && item.group !== prevGroup) {
        lines.push(rail("  " + violetSoft("● ") + bold(item.group)));
        prevGroup = item.group;
      }

      lines.push(rail("    " + renderItem(item, isCursor, isSelected)));
      const desc = renderDescription(item, isCursor);
      if (desc) lines.push(rail("    " + desc));
    });

    // Footer: live selection summary
    const count = selected.size;
    const totalTokens = items
      .filter((i) => selected.has(i.value))
      .reduce((acc, i) => acc + (i.tokens || 0), 0);
    const tokenLabel =
      totalTokens >= 1000
        ? `${(totalTokens / 1000).toFixed(1).replace(/\.0$/, "")}k tokens`
        : `${totalTokens} tokens`;
    lines.push(rail());
    lines.push(
      rail(
        `  ${violet("➤")} ${bold(`${count} selected`)}  ${graphite("·")}  ${violetSoft(tokenLabel)}`,
      ),
    );
    return lines;
  }

  function render(initial = false) {
    const lines = buildView();
    if (!initial && lastRenderedLines > 0) {
      // Move up to start of previous render and erase down
      stdout.write(moveUp(lastRenderedLines) + moveCol1 + ERASE_DOWN);
    }
    stdout.write(lines.join("\n") + "\n");
    lastRenderedLines = lines.length;
  }

  // Set up raw mode
  if (stdin.setRawMode) stdin.setRawMode(true);
  stdin.resume();
  stdin.setEncoding("utf8");
  stdout.write(HIDE_CURSOR);

  render(true);

  return new Promise((resolve, reject) => {
    function onKey(buf) {
      const key = buf.toString();

      // Ctrl-C / Esc → cancel
      if (key === "" || key === "") {
        cancelled = true;
        cleanup();
        reject(new Error("Selection cancelled by user"));
        return;
      }

      // Enter → confirm
      if (key === "\r" || key === "\n") {
        confirmed = true;
        cleanup();
        resolve(items.filter((i) => selected.has(i.value)).map((i) => i.value));
        return;
      }

      // Arrow keys (escape sequences)
      if (key === "[A" || key === "k") {
        cursor = (cursor - 1 + items.length) % items.length;
        render();
        return;
      }
      if (key === "[B" || key === "j") {
        cursor = (cursor + 1) % items.length;
        render();
        return;
      }

      // Space → toggle current
      if (key === " ") {
        const item = items[cursor];
        if (!item.required) {
          if (selected.has(item.value)) selected.delete(item.value);
          else selected.add(item.value);
        }
        render();
        return;
      }

      // 'a' → toggle all (preserving required)
      if (key === "a" || key === "A") {
        const allOn = items.every(
          (i) => i.required || selected.has(i.value),
        );
        for (const it of items) {
          if (it.required) continue;
          if (allOn) selected.delete(it.value);
          else selected.add(it.value);
        }
        render();
        return;
      }

      // Home/End
      if (key === "[H") { cursor = 0; render(); return; }
      if (key === "[F") { cursor = items.length - 1; render(); return; }
    }

    function cleanup() {
      stdin.removeListener("data", onKey);
      stdout.write(SHOW_CURSOR);
      if (stdin.setRawMode) stdin.setRawMode(false);
      stdin.pause();
    }

    stdin.on("data", onKey);
  });
}

/**
 * Single-choice selector with the same arrow-key UX.
 */
export async function singleSelect({ title, subtitle, items, defaultIndex = 0 } = {}) {
  if (!stdin.isTTY) {
    return items[defaultIndex]?.value;
  }
  let cursor = defaultIndex;
  let lastRenderedLines = 0;

  function build() {
    const lines = [];
    lines.push(rail());
    lines.push(violet(GLYPHS.diamond) + "  " + bold(title));
    if (subtitle) lines.push(rail("  " + graphite(subtitle)));
    lines.push(rail("  " + graphite("↑↓ navigate · enter confirm · esc cancel")));
    lines.push(rail());
    items.forEach((item, idx) => {
      const isCursor = idx === cursor;
      const cursorMark = isCursor ? violet("❯") : " ";
      const dot = isCursor
        ? rgb(PALETTE.success) + GLYPHS.circle + RESET
        : graphite(GLYPHS.circleOpen);
      const label = isCursor ? bold(violetSoft(item.label)) : item.label;
      const tag = item.recommended ? "  " + violetSoft("recommended") : "";
      const sub = item.description ? "\n      " + graphite(item.description) : "";
      lines.push(rail(`    ${cursorMark} ${dot} ${label}${tag}${sub.split("\n")[0]}`));
      if (sub) {
        const subLines = sub.split("\n").slice(1);
        for (const sl of subLines) lines.push(rail("    " + sl));
      }
    });
    lines.push(rail());
    return lines;
  }

  function render(initial = false) {
    const lines = build();
    if (!initial && lastRenderedLines > 0) {
      stdout.write(moveUp(lastRenderedLines) + moveCol1 + ERASE_DOWN);
    }
    stdout.write(lines.join("\n") + "\n");
    lastRenderedLines = lines.length;
  }

  if (stdin.setRawMode) stdin.setRawMode(true);
  stdin.resume();
  stdin.setEncoding("utf8");
  stdout.write(HIDE_CURSOR);
  render(true);

  return new Promise((resolve, reject) => {
    function cleanup() {
      stdin.removeListener("data", onKey);
      stdout.write(SHOW_CURSOR);
      if (stdin.setRawMode) stdin.setRawMode(false);
      stdin.pause();
    }
    function onKey(buf) {
      const key = buf.toString();
      if (key === "" || key === "") { cleanup(); reject(new Error("cancelled")); return; }
      if (key === "\r" || key === "\n") { cleanup(); resolve(items[cursor].value); return; }
      if (key === "[A" || key === "k") { cursor = (cursor - 1 + items.length) % items.length; render(); return; }
      if (key === "[B" || key === "j") { cursor = (cursor + 1) % items.length; render(); return; }
    }
    stdin.on("data", onKey);
  });
}
