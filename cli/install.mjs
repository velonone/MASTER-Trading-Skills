#!/usr/bin/env node
/**
 * MASTER Trading Skills Installer
 * Install individual skills to AI agent platforms.
 *
 * Usage:
 *   npx master-trading-skills
 *   npx master-trading-skills --agent=kimi-code --skills=core,inference --method=symlink
 *   npx master-trading-skills --skills=full --agent=claude-code --calibration=snapshot
 */

import { existsSync, mkdirSync, writeFileSync, readFileSync } from "fs";
import { join, dirname, resolve } from "path";
import { fileURLToPath } from "url";
import { detectAgents, resolveInstallPath } from "./lib/agents.mjs";
import { discoverSkills, resolveDependencies, getSkillById } from "./lib/skills.mjs";
import { installSkill, createSkillManifest } from "./lib/installer.mjs";
import { ask, askChoice, askMultiSelect, closePrompt } from "./lib/prompt.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const REPO_ROOT = resolve(join(__dirname, ".."));

// ---------------------------------------------------------------------------
// Read package metadata so the installer never lies about its own version.
// ---------------------------------------------------------------------------
let PKG = { version: "unknown", name: "master-trading-skills" };
try {
  PKG = JSON.parse(readFileSync(join(REPO_ROOT, "package.json"), "utf8"));
} catch {
  /* fall through */
}

// Read calibration provenance directly from the snapshot data file so the
// installer reports the *actual* bundled calibration, not a constant.
let CALIBRATION_VERSION = "unknown";
let CALIBRATION_RELEASED = "unknown";
try {
  const calFile = readFileSync(
    join(REPO_ROOT, "skills", "inference", "_calibration_data.py"),
    "utf8",
  );
  const v = calFile.match(/"version":\s*"([^"]+)"/);
  const r = calFile.match(/"released_at":\s*"([^"]+)"/);
  if (v) CALIBRATION_VERSION = v[1];
  if (r) CALIBRATION_RELEASED = r[1];
} catch {
  /* fall through */
}

const REPO_URL = (PKG.repository && PKG.repository.url) || "https://github.com/velonone/MASTER-Trading-Skills";

const BANNER = `
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         master-trading-skills · v${PKG.version.padEnd(28)}║
║                                                               ║
║   Open-source trading skills for AI agents — by VelonLabs     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
`;

const DISCLAIMER = `
─── Risk Disclaimer ────────────────────────────────────────────
This software is provided "as is" for research and educational
use. It is NOT financial advice and does NOT guarantee profits.

Trading and DeFi interactions can result in TOTAL LOSS of your
funds. The bundled VelonLabs Reference Calibration is a snapshot
of historically observed values; markets evolve and any number
in this codebase may be out of date.

Default values shown anywhere in this package are STARTING POINTS,
not absolutes. Always backtest and validate against your own data
before running live capital, and prefer testnet/sandbox mode while
exploring.

By installing you accept the MIT license terms (see LICENSE) and
acknowledge the limitations above.
────────────────────────────────────────────────────────────────
`;

const CALIBRATION_NOTE = `
─── Calibration Setup ─────────────────────────────────────────
The inference layer reads confidence values from a calibration
source. The bundled VelonLabs Reference Snapshot v${CALIBRATION_VERSION}
(released ${CALIBRATION_RELEASED}) is used by default — these are
real values, not placeholders, but they age over time.

Sources you can choose:
  • snapshot     bundled VelonLabs reference (free, default)
  • live         monthly subscription (paid, current values)
  • self         your own calibration via tools/calibrate.py
  • custom       a JSON file matching the snapshot schema
  • placeholder  all confidences = 0.5 (testing only)

Configure now (saves to ~/.master-trading/config.json):
  python -m skills.inference set snapshot
  python -m skills.inference set custom --path=./my-calibration.json
  python -m skills.inference set live --api-key=...

Or skip — every inference output carries a _meta block telling you
which calibration produced it. Your agent can ask you later.
────────────────────────────────────────────────────────────────
`;

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = {};
  for (const arg of args) {
    if (arg.startsWith("--")) {
      const [key, value] = arg.slice(2).split("=");
      parsed[key] = value || true;
    }
  }
  return parsed;
}

function printNextSteps(agentId, installPath) {
  console.log(`
─── Next Steps ─────────────────────────────────────────────────

1. Verify install
     python -c "from skills.core.registry import registry; \\
                registry.auto_discover('skills'); \\
                print(list(registry.list_skills().keys()))"

2. (Optional) Pick a calibration source
     python -m skills.inference show           # see current
     python -m skills.inference prompt         # show choice prompt
     python -m skills.inference set snapshot   # persist

3. Try the agent tool surface
     python examples/example_agent_tools.py

4. Read the docs
     SKILL.md          — full reference
     SKILL_LITE.md     — quick reference for context-limited agents
     docs/tutorials/   — getting started, backtesting, web3, llm-agent

5. Report issues
     ${REPO_URL.replace(/\.git$/, "")}/issues

Powered by VelonLabs Trading Skills · MIT License
────────────────────────────────────────────────────────────────
`);
}

async function main() {
  console.log(BANNER);

  const args = parseArgs();

  console.log(`Source:      ${REPO_URL}`);
  console.log(`Version:     ${PKG.version}`);
  console.log(`Calibration: VelonLabs Reference Snapshot v${CALIBRATION_VERSION} (${CALIBRATION_RELEASED})`);

  // Discover skills
  const skills = discoverSkills();
  console.log(`\nFound ${skills.filter((s) => !s.isMeta).length} skill packages.\n`);

  // Detect agents
  const agents = detectAgents();
  if (agents.length === 0) {
    console.log("No supported AI agent platforms detected on this machine.");
    console.log("Supported: Kimi Code CLI, Claude Code, Cursor, Cline, GitHub Copilot, Codex.");
    console.log("You can still install to a custom path with --target=/path/to/skills.");
  }

  // ---------------- Select skills ----------------
  let selectedSkillIds;
  if (args.skills) {
    selectedSkillIds = args.skills.split(",").map((s) => s.trim());
  } else {
    const skillOptions = skills.map((s) => ({
      value: s.id,
      label: s.name,
      description: s.description,
      required: s.required || false,
      isMeta: s.isMeta || false,
    }));
    selectedSkillIds = await askMultiSelect("Select skills to install", skillOptions);
  }

  // Resolve dependencies
  const resolvedIds = resolveDependencies(selectedSkillIds);
  const resolvedSkills = resolvedIds.map((id) => getSkillById(id)).filter(Boolean);

  console.log("\nSelected skills:");
  for (const s of resolvedSkills) {
    console.log(`  • ${s.name}`);
  }

  // ---------------- Select agent ----------------
  let agentId;
  let installPath;
  let scope = "project";

  if (args.agent) {
    agentId = args.agent;
  } else if (agents.length === 1) {
    agentId = agents[0].id;
    console.log(`\nDetected agent: ${agents[0].name}`);
  } else if (agents.length > 1) {
    const agentOptions = agents.map((a) => ({ value: a.id, label: a.name }));
    agentOptions.push({ value: "custom", label: "Custom path" });
    agentId = await askChoice("Which agent do you want to install to?", agentOptions);
  } else {
    agentId = "custom";
  }

  if (agentId === "custom" || args.target) {
    installPath = args.target || process.cwd();
    scope = "custom";
  } else {
    const agent = agents.find((a) => a.id === agentId);
    if (agent && agent.hasGlobal && agent.hasProject) {
      scope = await askChoice("Installation scope?", [
        { value: "project", label: "Project (current directory)", recommended: true },
        { value: "global", label: "Global (user home)" },
      ]);
    } else if (agent && agent.hasProject) {
      scope = "project";
    } else if (agent && agent.hasGlobal) {
      scope = "global";
    }
    installPath = resolveInstallPath(agentId, scope);
  }

  if (!installPath) {
    console.error("Could not resolve installation path.");
    process.exit(1);
  }

  if (!existsSync(installPath)) {
    mkdirSync(installPath, { recursive: true });
  }

  // ---------------- Select method ----------------
  let method = args.method;
  if (!method) {
    method = await askChoice("Installation method?", [
      { value: "symlink", label: "Symlink (recommended) — auto-updates when repo changes", recommended: true },
      { value: "copy", label: "Copy — standalone, no dependency on repo" },
    ]);
  }

  // ---------------- Install ----------------
  console.log(`\nInstalling to: ${installPath}`);
  console.log(`Method:        ${method}\n`);

  const installed = [];
  for (const skill of resolvedSkills) {
    try {
      const result = installSkill(skill, installPath, method);
      installed.push({ skill, ...result });
      console.log(`  ✓ ${skill.name} -> ${result.name}`);
    } catch (err) {
      console.error(`  ✗ ${skill.name}: ${err.message}`);
    }
  }

  // ---------------- Manifest ----------------
  const { manifest, manifestPath } = createSkillManifest(installed, installPath);
  // Augment manifest with calibration provenance + attribution.
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
  console.log(`\nManifest written: ${manifestPath}`);

  // ---------------- Summary ----------------
  console.log(`\nInstallation complete:
  Agent:  ${agentId} (${scope})
  Method: ${method}
  Path:   ${installPath}
  Skills: ${installed.length} package(s)`);

  // ---------------- Calibration note ----------------
  if (resolvedIds.includes("inference") || resolvedIds.includes("full")) {
    console.log(CALIBRATION_NOTE);
  }

  // ---------------- Disclaimer (always shown) ----------------
  console.log(DISCLAIMER);

  // ---------------- Next steps ----------------
  printNextSteps(agentId, installPath);

  closePrompt();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
