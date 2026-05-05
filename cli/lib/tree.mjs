/**
 * Skill Tree Renderer
 * ====================
 * Renders the skill catalog as a grouped tree with selection markers,
 * dependency hints, token costs, and a feature summary per node. The
 * top-level layout is grouped by `group` (Foundation, Signals, …) so
 * the user sees the architecture before deciding what to install.
 */

import {
  bold,
  dim,
  graphite,
  muted,
  rgb,
  PALETTE,
  RESET,
  violet,
  violetSoft,
  GLYPHS,
} from "./colors.mjs";
import { GROUPS } from "./skills.mjs";

const REQUIRED_TAG = rgb(PALETTE.warning) + "[REQUIRED]" + RESET;

function tokenLabel(n) {
  if (n >= 1000) return `${(n / 1000).toFixed(1).replace(/\.0$/, "")}k tokens`;
  return `${n} tokens`;
}

function depsLabel(skill) {
  if (!skill.dependsOn || skill.dependsOn.length === 0) return "";
  return `needs ${skill.dependsOn.join(" + ")}`;
}

/**
 * Render the catalog tree.
 *
 * @param {Array<object>} skills        — full SKILL_PACKAGES list (already filtered).
 * @param {Set<string>}   selectedIds   — currently selected skill ids.
 * @param {object}        [opts]
 * @param {boolean}       [opts.showFeatures=true]
 * @returns {string[]}                  — array of lines (for caller to print).
 */
export function renderSkillTree(skills, selectedIds, { showFeatures = true } = {}) {
  const lines = [];
  const grouped = new Map();
  for (const g of GROUPS) grouped.set(g.id, []);
  for (const s of skills) {
    if (!grouped.has(s.group)) grouped.set(s.group, []);
    grouped.get(s.group).push(s);
  }

  let displayIndex = 0;
  const indexById = new Map();
  const groupKeys = [...grouped.keys()].filter((k) => grouped.get(k).length > 0);

  for (let gi = 0; gi < groupKeys.length; gi++) {
    const groupId = groupKeys[gi];
    const groupItems = grouped.get(groupId);
    const groupMeta = GROUPS.find((g) => g.id === groupId);
    const groupLabel = groupMeta ? groupMeta.label : groupId;
    const isLastGroup = gi === groupKeys.length - 1;

    lines.push("");
    lines.push(violetSoft("● ") + bold(groupLabel));

    for (let i = 0; i < groupItems.length; i++) {
      const skill = groupItems[i];
      const isLastInGroup = i === groupItems.length - 1;
      const branch = isLastInGroup ? GLYPHS.treeLast : GLYPHS.treeBranch;

      displayIndex += 1;
      indexById.set(skill.id, displayIndex);

      const num = dim(`[${String(displayIndex).padStart(2, " ")}]`);
      const isSelected = selectedIds.has(skill.id);
      const marker = isSelected
        ? rgb(PALETTE.success) + GLYPHS.check + RESET
        : violet(GLYPHS.circleOpen);

      const titleLine = [
        graphite(branch),
        num,
        marker,
        bold(skill.name),
        skill.required ? REQUIRED_TAG : "",
      ].filter(Boolean).join(" ");
      lines.push("  " + titleLine);

      // Sub-line: description + meta
      const indentChar = isLastInGroup ? " " : graphite(GLYPHS.treeVert);
      const meta = [
        skill.dependsOn && skill.dependsOn.length
          ? muted(depsLabel(skill))
          : null,
        muted(tokenLabel(skill.tokens || 0)),
      ].filter(Boolean).join(muted(" · "));

      lines.push(`  ${indentChar}      ${graphite(skill.description)}`);
      if (meta) {
        lines.push(`  ${indentChar}      ${meta}`);
      }

      // Optional feature bullets
      if (showFeatures && skill.features && skill.features.length) {
        for (const f of skill.features.slice(0, 4)) {
          lines.push(`  ${indentChar}        ${dim("·")} ${graphite(f)}`);
        }
      }

      // Spacer between skills inside the same group
      if (!isLastInGroup) lines.push(`  ${indentChar}`);
    }
  }

  lines.push("");
  return { lines, indexById };
}

/**
 * Render a compact summary line listing currently-selected skills.
 */
export function renderSelectionSummary(skills, selectedIds) {
  const total = [...selectedIds].length;
  if (total === 0) return graphite("  no skills selected yet");
  const tokenSum = skills
    .filter((s) => selectedIds.has(s.id))
    .reduce((acc, s) => acc + (s.tokens || 0), 0);
  return (
    "  " +
    violet(`${total} selected`) +
    muted(" · ") +
    violetSoft(tokenLabel(tokenSum)) +
    muted(" · ") +
    graphite([...selectedIds].join(", "))
  );
}

/**
 * Detected-agent panel.
 */
export function renderAgentPanel(detected, allDefinitions) {
  const lines = [];
  lines.push("");
  lines.push(violetSoft("●") + " " + bold("Available agent runtimes"));
  lines.push("");

  const detectedIds = new Set(detected.map((a) => a.id));
  let idx = 0;
  for (const def of allDefinitions) {
    idx += 1;
    const found = detected.find((a) => a.id === def.id);
    const num = dim(`[${String(idx).padStart(2, " ")}]`);
    if (found) {
      const scopes = [];
      if (found.hasGlobal) scopes.push(violetSoft("global"));
      if (found.hasProject) scopes.push(violetSoft("project"));
      const where = found.foundGlobal[0] || found.foundProject[0] || "";
      lines.push(
        `  ${num} ${rgb(PALETTE.success)}${GLYPHS.circle}${RESET}  ${bold(def.name).padEnd(20)} ${graphite(where)}  ${scopes.join(graphite(" · "))}`,
      );
    } else {
      lines.push(
        `  ${num} ${graphite(GLYPHS.dash)}  ${graphite(def.name).padEnd(20)} ${dim("not detected")}`,
      );
    }
  }
  // Custom path option
  idx += 1;
  lines.push("");
  lines.push(`  ${dim(`[${String(idx).padStart(2, " ")}]`)} ${violet("◆")}  ${bold("Custom path…")}  ${graphite("type your own absolute path")}`);
  lines.push("");
  return { lines, customIndex: idx };
}
