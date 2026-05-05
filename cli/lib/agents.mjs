/**
 * Agent Environment Detection
 * Detects installed AI agent platforms and their skill directories.
 */

import { homedir } from "os";
import { existsSync } from "fs";
import { join } from "path";

const HOME = homedir();
const CWD = process.cwd();

export const AGENT_DEFINITIONS = [
  {
    id: "kimi-code",
    name: "Kimi Code CLI",
    globalPaths: [
      join(HOME, ".codex", "skills"),
      join(HOME, "AppData", "Roaming", "Antigravity", "User", "globalStorage", "moonshot-ai.kimi-code", "skills"),
    ],
    projectPaths: [".codex/skills", ".kimi/skills"],
  },
  {
    id: "claude-code",
    name: "Claude Code",
    globalPaths: [join(HOME, ".claude", "skills")],
    projectPaths: [".claude/skills"],
  },
  {
    id: "cursor",
    name: "Cursor",
    globalPaths: [join(HOME, ".cursor", "skills")],
    projectPaths: [".cursor/skills"],
  },
  {
    id: "cline",
    name: "Cline",
    globalPaths: [join(HOME, ".cline", "skills")],
    projectPaths: [".cline/skills"],
  },
  {
    id: "github-copilot",
    name: "GitHub Copilot",
    globalPaths: [join(HOME, ".github", "copilot", "skills")],
    projectPaths: [".github/copilot/skills"],
  },
  {
    id: "codex",
    name: "Codex (OpenAI)",
    globalPaths: [join(HOME, ".codex", "skills")],
    projectPaths: [".codex/skills"],
  },
];

export function detectAgents() {
  const detected = [];
  for (const agent of AGENT_DEFINITIONS) {
    const foundGlobal = agent.globalPaths.filter((p) => existsSync(p));
    const foundProject = agent.projectPaths.filter((p) => existsSync(join(CWD, p)));
    if (foundGlobal.length > 0 || foundProject.length > 0) {
      detected.push({
        ...agent,
        foundGlobal,
        foundProject,
        hasGlobal: foundGlobal.length > 0,
        hasProject: foundProject.length > 0,
      });
    }
  }
  return detected;
}

export function resolveInstallPath(agentId, scope = "project") {
  const agent = AGENT_DEFINITIONS.find((a) => a.id === agentId);
  if (!agent) return null;

  if (scope === "global") {
    for (const p of agent.globalPaths) {
      if (existsSync(p)) return p;
    }
    // Fallback to first global path even if not exists yet
    return agent.globalPaths[0] || null;
  }

  // Project scope
  for (const p of agent.projectPaths) {
    const full = join(CWD, p);
    if (existsSync(full)) return full;
  }
  // Fallback to first project path
  return agent.projectPaths[0] ? join(CWD, agent.projectPaths[0]) : null;
}
