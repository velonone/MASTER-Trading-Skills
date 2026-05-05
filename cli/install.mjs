#!/usr/bin/env node
/**
 * MASTER Trading Skills Installer
 * ================================
 * VelonLabs · MIT
 *
 * Usage (until published to npm):
 *   npx github:velonone/MASTER-Trading-Skills
 *   npx github:velonone/MASTER-Trading-Skills --skills=full --agent=claude-code --method=symlink --yes
 *
 * Flags:
 *   --skills=core,inference,…   pre-select skill ids (or "full")
 *   --agent=<id>                pre-select an agent (or "custom")
 *   --target=<abs-path>         only used when --agent=custom
 *   --method=symlink|copy       installation method
 *   --yes                       skip interactive confirmation
 */

import { existsSync, mkdirSync, writeFileSync, readFileSync } from "fs";
import { join, dirname, resolve } from "path";
import { fileURLToPath } from "url";

import { AGENT_DEFINITIONS, detectAgents, resolveInstallPath } from "./lib/agents.mjs";
import { discoverSkills, resolveDependencies, getSkillById } from "./lib/skills.mjs";
import { installSkill, createSkillManifest } from "./lib/installer.mjs";
import { ask, closePrompt } from "./lib/prompt.mjs";
import { multiSelect, singleSelect } from "./lib/multiselect.mjs";
import { animateBanner, renderBanner, Ceremony } from "./lib/banner.mjs";
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
} from "./lib/colors.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const REPO_ROOT = resolve(join(__dirname, ".."));

// ───────────────────────────── metadata ─────────────────────────────

let PKG = { version: "unknown", name: "master-trading-skills" };
try { PKG = JSON.parse(readFileSync(join(REPO_ROOT, "package.json"), "utf8")); } catch {}

let CALIBRATION_VERSION = "unknown";
let CALIBRATION_RELEASED = "unknown";
try {
  const calFile = readFileSync(join(REPO_ROOT, "skills", "inference", "_calibration_data.py"), "utf8");
  const v = calFile.match(/"version":\s*"([^"]+)"/);
  const r = calFile.match(/"released_at":\s*"([^"]+)"/);
  if (v) CALIBRATION_VERSION = v[1];
  if (r) CALIBRATION_RELEASED = r[1];
} catch {}

const REPO_URL =
  (PKG.repository && PKG.repository.url) ||
  "https://github.com/velonone/MASTER-Trading-Skills";

// ───────────────────────────── arg parser ─────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = {};
  for (const arg of args) {
    if (arg.startsWith("--")) {
      const [key, value] = arg.slice(2).split("=");
      parsed[key] = value === undefined ? true : value;
    }
  }
  return parsed;
}

// ─────────────────────────── disclaimer + epilogue ───────────────────────────

const DISCLAIMER_LINES = [
  "Not financial advice and no warranty. Trading and DeFi can result",
  "in TOTAL LOSS of your funds. The bundled VelonLabs Reference",
  "Calibration is a snapshot of historically observed values; markets",
  "evolve and any number in this codebase may be out of date.",
  "",
  "Default values are STARTING POINTS, not absolutes. Always backtest",
  "and validate against your own data before risking live capital.",
];

function printDisclaimer(ceremony) {
  ceremony.section("Risk disclaimer");
  for (const l of DISCLAIMER_LINES) ceremony.line(l);
}

function printNextSteps(ceremony, agentId, installPath) {
  ceremony.section("Next steps");
  ceremony.line(graphite("1. Verify installation"));
  ceremony.line('   python -c "from skills.core.registry import registry; \\');
  ceremony.line('              registry.auto_discover(' + violetSoft("'skills'") + "); \\");
  ceremony.line('              print(list(registry.list_skills().keys()))"');
  ceremony.line("");
  ceremony.line(graphite("2. (Optional) Pick a calibration source"));
  ceremony.line(`   ${violet("python -m skills.inference show")}`);
  ceremony.line(`   ${violet("python -m skills.inference set snapshot")}`);
  ceremony.line("");
  ceremony.line(graphite("3. Read the docs"));
  ceremony.line(`   ${violetSoft("SKILL.md")} — full reference`);
  ceremony.line(`   ${violetSoft("SKILL_LITE.md")} — quick reference for context-limited agents`);
  ceremony.line("");
  ceremony.line(graphite("4. Report issues"));
  ceremony.line(`   ${REPO_URL.replace(/\.git$/, "")}/issues`);
}

// ────────────────────────── ceremony orchestration ──────────────────────────

async function main() {
  const args = parseArgs();

  // ─── 1. Animated banner (rotating-gradient logo + framed box)
  await animateBanner({
    version: PKG.version,
    calibrationVersion: CALIBRATION_VERSION,
  });

  // ─── 2. Project tag pill
  const ceremony = new Ceremony("master-trading");
  ceremony.tagPill();

  // ─── 3. Source / repository line
  ceremony.section("Source", REPO_URL);

  // ─── 4. Calibration provenance
  ceremony.section("Calibration");
  ceremony.line(
    `${violetSoft("VelonLabs Reference Snapshot")} ${bold("v" + CALIBRATION_VERSION)} ` +
    graphite(`(released ${CALIBRATION_RELEASED})`),
  );
  ceremony.line(graphite("real values, not placeholders — change later via"));
  ceremony.line(`${violet("python -m skills.inference set <source>")}`);

  // ─── 5. Skill discovery
  const skills = discoverSkills();
  ceremony.section("Discover skills");
  ceremony.status(`${skills.filter((s) => !s.isMeta).length} skill packages available`);

  // ─── 6. Skill picker (interactive arrow-key checkboxes, or via flag)
  let selectedSkillIds;
  if (args.skills) {
    selectedSkillIds = String(args.skills).split(",").map((s) => s.trim());
    ceremony.section("Selected skills (from --skills flag)");
    for (const id of selectedSkillIds) {
      const s = getSkillById(id);
      if (s) ceremony.status(s.name);
    }
  } else {
    const items = skills.map((s) => ({
      value: s.id,
      label: s.name,
      description: s.description,
      group: s.group ? capitalise(s.group) : "Skills",
      required: !!s.required,
      tokens: s.tokens || 0,
      isMeta: !!s.isMeta,
    }));
    ceremony.line("");
    selectedSkillIds = await multiSelect({
      title: "Select skills to install",
      subtitle: "dependencies are auto-resolved",
      items,
    });
  }

  const resolvedIds = resolveDependencies(selectedSkillIds);
  const resolvedSkills = resolvedIds.map((id) => getSkillById(id)).filter(Boolean);
  if (resolvedIds.length !== selectedSkillIds.length) {
    ceremony.line(
      graphite("auto-included dependencies: ") +
      violetSoft(resolvedIds.filter((id) => !selectedSkillIds.includes(id)).join(", ") || "—"),
    );
  }

  // ─── 7. Agent target picker
  const detected = detectAgents();
  let agentId, scope = "project", installPath;

  if (args.agent) {
    agentId = args.agent;
    if (agentId === "custom") {
      installPath = args.target || process.cwd();
      scope = "custom";
    }
  } else {
    const detectedSet = new Set(detected.map((a) => a.id));
    const items = AGENT_DEFINITIONS.map((def) => {
      const found = detected.find((a) => a.id === def.id);
      const where = found
        ? (found.foundGlobal[0] || found.foundProject[0])
        : "";
      const tagBits = [];
      if (found?.hasGlobal) tagBits.push("global");
      if (found?.hasProject) tagBits.push("project");
      return {
        value: def.id,
        label: def.name + (found ? "  " + violetSoft(GLYPHS.circle) + " detected" : ""),
        description: found ? `${where}  ${graphite("·")} ${tagBits.join(" + ")}` : "not detected — will create on install",
      };
    });
    items.push({
      value: "custom",
      label: "Custom path…",
      description: "type your own absolute path",
    });

    ceremony.section("Detected agent runtimes", `${detected.length} found on this machine`);
    ceremony.line("");

    agentId = await singleSelect({
      title: "Where do you want to install the skills?",
      items,
      defaultIndex: detected.length > 0
        ? AGENT_DEFINITIONS.findIndex((a) => a.id === detected[0].id)
        : 0,
    });
  }

  if (agentId === "custom") {
    if (!installPath) {
      installPath = (await ask("Custom install path")) || process.cwd();
    }
    scope = "custom";
  } else {
    const agent = AGENT_DEFINITIONS.find((a) => a.id === agentId);
    if (agent && agent.globalPaths && agent.projectPaths) {
      const found = detected.find((a) => a.id === agentId);
      if (found?.hasGlobal && found?.hasProject) {
        scope = await singleSelect({
          title: "Installation scope",
          items: [
            { value: "project", label: "Project (current directory)", description: "scoped to this folder", recommended: true },
            { value: "global",  label: "Global (user home)",          description: "available to all projects" },
          ],
        });
      } else {
        scope = found?.hasGlobal ? "global" : "project";
      }
    }
    installPath = resolveInstallPath(agentId, scope);
  }

  if (!installPath) {
    console.error("\n  " + rgb(PALETTE.danger) + GLYPHS.cross + " could not resolve installation path." + RESET);
    process.exit(1);
  }
  if (!existsSync(installPath)) mkdirSync(installPath, { recursive: true });

  // ─── 8. Method
  let method = args.method;
  if (!method) {
    method = await singleSelect({
      title: "Installation method",
      items: [
        { value: "symlink", label: "Symlink", description: "auto-updates when the source repo changes", recommended: true },
        { value: "copy",    label: "Copy",    description: "standalone snapshot, no dependency on the repo" },
      ],
    });
  }

  // ─── 9. Confirm
  ceremony.section("Ready to install");
  ceremony.field("agent", `${bold(agentId)} ${graphite(`(${scope})`)}`);
  ceremony.field("path", graphite(installPath));
  ceremony.field("method", method);
  ceremony.field("skills", `${resolvedSkills.length} packages`);
  ceremony.field("calibration", `v${CALIBRATION_VERSION}`);

  if (!args.yes) {
    ceremony.line("");
    const proceed = await singleSelect({
      title: "Proceed?",
      items: [
        { value: true,  label: "Yes — install now" },
        { value: false, label: "Cancel" },
      ],
    });
    if (!proceed) {
      ceremony.section("Cancelled", "no files were touched");
      closePrompt();
      return;
    }
  }

  // ─── 10. Install
  ceremony.section("Installing", `${resolvedSkills.length} skills → ${installPath}`);
  const installed = [];
  for (const skill of resolvedSkills) {
    try {
      const result = installSkill(skill, installPath, method);
      installed.push({ skill, ...result });
      ceremony.status(`${skill.name}  ${graphite("→ " + result.name)}`, "done");
    } catch (err) {
      ceremony.status(`${skill.name}  ${graphite(err.message)}`, "fail");
    }
  }

  // ─── 11. Manifest
  const { manifest, manifestPath } = createSkillManifest(installed, installPath);
  manifest.installerVersion = PKG.version;
  manifest.calibration = {
    bundled_version: CALIBRATION_VERSION,
    released_at: CALIBRATION_RELEASED,
    source: "velonlabs_reference_snapshot",
    attribution: "VelonLabs Reference Calibration",
  };
  manifest.attribution = "Powered by VelonLabs Trading Skills (MIT)";
  manifest.disclaimer_acknowledged = true;
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  ceremony.section("Manifest");
  ceremony.line(graphite(manifestPath));

  // ─── 12. Disclaimer + next steps
  printDisclaimer(ceremony);
  printNextSteps(ceremony, agentId, installPath);

  ceremony.section("Done", `installed ${installed.length} skill packages — ${violetSoft("Powered by VelonLabs · MIT")}`);
  ceremony.close();

  closePrompt();
}

function capitalise(s) {
  if (!s) return s;
  return s[0].toUpperCase() + s.slice(1);
}

main().catch((err) => {
  console.error("\n" + rgb(PALETTE.danger) + GLYPHS.cross + RESET + " " + err.message);
  process.exit(1);
});
