/**
 * Skill Catalog
 * ==============
 * Enriched catalog of all installable skill packages, including a
 * lightweight tree structure for the picker UI (parent groupings,
 * sub-features, token cost, dependency edges, citations).
 */

import { existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const REPO_ROOT = join(__dirname, "..", "..");

export const SKILL_PACKAGES = [
  {
    id: "core",
    name: "Core Abstraction",
    description: "Universal types · base classes · skill registry",
    path: "skills/core",
    required: true,
    tokens: 4400,
    group: "foundation",
    features: [
      "Signal · Order · Position · ExecutionReport · RiskLimit",
      "BaseStrategy · BaseRiskManager · BaseConnector",
      "SkillRegistry with auto-discovery",
      "Structured logging (master.* namespace)",
    ],
  },
  {
    id: "inference",
    name: "Higher-Order Inference",
    description: "Causal-chain reasoning, singularity detection, calibration",
    path: "skills/inference",
    dependsOn: ["core"],
    tokens: 7400,
    group: "intelligence",
    features: [
      "8 inference primitives with empirical accuracy tracking",
      "5 causal-chain types (whale · protocol · listing · hack · liquidation)",
      "Backward induction + counterfactual analysis",
      "VelonLabs Reference Calibration v2026.05",
    ],
  },
  {
    id: "signals-technical",
    name: "Signals — Technical",
    description: "Order-book microstructure + Kelly sizing",
    path: "skills/signals/technical",
    dependsOn: ["core"],
    tokens: 2200,
    group: "signals",
    features: [
      "Order Book Imbalance (Stoikov 2018)",
      "Funding Rate Arbitrage",
      "Kelly Position Sizer (Thorp 2006)",
    ],
  },
  {
    id: "signals-advanced",
    name: "Signals — Advanced Math",
    description: "TDA, chaos theory, adversarial RL, GP evolution",
    path: "skills/signals",
    dependsOn: ["core", "signals-technical"],
    excludePaths: ["skills/signals/__init__.py"],
    tokens: 4400,
    group: "signals",
    features: [
      "TDA crash detection (Gidea & Katz 2018)",
      "Lyapunov exponent regime detection (Rosenstein 1993)",
      "Adversarial RL market maker (Spooner 2020)",
      "Genetic-programming alpha evolution (Koza 1992)",
    ],
  },
  {
    id: "execution",
    name: "Execution Layer (CEX)",
    description: "CCXT connector · OMS · risk manager · pipeline",
    path: "skills/execution",
    dependsOn: ["core"],
    tokens: 6200,
    group: "execution",
    features: [
      "CCXT Pro connector (Binance · Bybit · OKX)",
      "Order Management System with PnL persistence",
      "Dynamic Risk Manager (drawdown · leverage · velocity)",
      "TradingPipeline orchestrator (Signal → Risk → OMS → Conn)",
    ],
  },
  {
    id: "execution-web3",
    name: "Execution — Web3 / DeFi",
    description: "DEX executor with MEV protection",
    path: "skills/execution/web3",
    dependsOn: ["core", "execution"],
    tokens: 1800,
    group: "execution",
    features: [
      "Async Web3 v7 integration (EIP-1559 gas)",
      "Flashbots Protect / MEV Blocker / Eden routing",
      "swap_exact_in stub guard (production-safe)",
    ],
  },
  {
    id: "adversarial",
    name: "Adversarial Intelligence",
    description: "FOMO sentiment + on-chain whale tracking",
    path: "skills/adversarial",
    dependsOn: ["core"],
    tokens: 3400,
    group: "intelligence",
    features: [
      "FOMO / panic detector",
      "Whale accumulation/distribution classifier",
      "Etherscan integration ready",
    ],
  },
  {
    id: "backtest",
    name: "Backtest Engine",
    description: "Vectorised, lookahead-free strategy validation",
    path: "backtest",
    dependsOn: ["core"],
    tokens: 3700,
    group: "validation",
    features: [
      "Bar-by-bar vectorised engine",
      "Almgren-Chriss simplified slippage",
      "Sharpe · Sortino · Calmar · MaxDD · Profit Factor",
      "Lookahead-free fills (regression-tested)",
    ],
  },
  {
    id: "agent",
    name: "LLM Agent Adapter",
    description: "Tool schema + capability gate + audit log",
    path: "skills/agent",
    dependsOn: ["core"],
    tokens: 1800,
    group: "integration",
    features: [
      "Anthropic Messages · OpenAI Responses · Kimi tools",
      "AgentPolicy gate (capability · blocklist · budget)",
      "Per-call audit log",
      "Schema typing for Optional · Decimal · Literal · Enum",
    ],
  },
  {
    id: "full",
    name: "Full Pack",
    description: "Install everything below",
    path: ".",
    isMeta: true,
    tokens: 35400,
    group: "preset",
    features: ["All skills · ~35.4k context tokens · ~4.5 MB on disk"],
  },
];

// Group taxonomy used by the tree renderer.
export const GROUPS = [
  { id: "foundation",  label: "Foundation" },
  { id: "intelligence", label: "Intelligence" },
  { id: "signals",     label: "Signals" },
  { id: "execution",   label: "Execution" },
  { id: "validation",  label: "Validation" },
  { id: "integration", label: "Integration" },
  { id: "preset",      label: "Preset" },
];

export function discoverSkills() {
  const available = [];
  for (const skill of SKILL_PACKAGES) {
    const fullPath = join(REPO_ROOT, skill.path);
    if (skill.isMeta || existsSync(fullPath)) {
      available.push(skill);
    }
  }
  return available;
}

export function resolveDependencies(selectedIds) {
  if (selectedIds.includes("full")) {
    return SKILL_PACKAGES.filter((s) => !s.isMeta).map((s) => s.id);
  }

  const resolved = new Set(selectedIds);
  const toProcess = [...selectedIds];
  while (toProcess.length > 0) {
    const id = toProcess.pop();
    const skill = SKILL_PACKAGES.find((s) => s.id === id);
    if (skill && skill.dependsOn) {
      for (const dep of skill.dependsOn) {
        if (!resolved.has(dep)) {
          resolved.add(dep);
          toProcess.push(dep);
        }
      }
    }
  }
  resolved.add("core");
  return Array.from(resolved).filter((id) => id !== "full");
}

export function getSkillById(id) {
  return SKILL_PACKAGES.find((s) => s.id === id);
}
