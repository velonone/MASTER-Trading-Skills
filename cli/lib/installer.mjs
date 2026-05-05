/**
 * Skill Installation Logic
 * Supports symlink and copy methods.
 */

import { mkdirSync, existsSync, copyFileSync, readdirSync, statSync, symlinkSync, rmSync, readFileSync } from "fs";
import { join, resolve, relative } from "path";
import { fileURLToPath } from "url";
import { dirname } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const REPO_ROOT = resolve(join(__dirname, "..", ".."));

function ensureDir(dir) {
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
}

function copyDir(src, dest, exclude = []) {
  ensureDir(dest);
  const entries = readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = join(src, entry.name);
    const destPath = join(dest, entry.name);

    if (exclude.some((ex) => srcPath.includes(ex))) continue;

    if (entry.isDirectory()) {
      copyDir(srcPath, destPath, exclude);
    } else {
      copyFileSync(srcPath, destPath);
    }
  }
}

function symlinkDir(src, dest) {
  ensureDir(dirname(dest));
  if (existsSync(dest)) {
    rmSync(dest, { recursive: true, force: true });
  }
  symlinkSync(src, dest, "junction");
}

export function installSkill(skill, targetDir, method = "symlink") {
  const src = resolve(join(REPO_ROOT, skill.path));
  const destName = `master-trading-${skill.id}`;
  const dest = join(targetDir, destName);

  if (!existsSync(src)) {
    throw new Error(`Source path does not exist: ${src}`);
  }

  ensureDir(targetDir);

  if (method === "symlink") {
    symlinkDir(src, dest);
  } else {
    const exclude = skill.excludePaths || [];
    copyDir(src, dest, exclude);
  }

  return { src, dest, method, name: destName };
}

function readPackageVersion() {
  try {
    const pkgPath = resolve(join(REPO_ROOT, "package.json"));
    if (existsSync(pkgPath)) {
      const pkg = JSON.parse(readFileSync(pkgPath, "utf8"));
      return pkg.version || "unknown";
    }
  } catch {
    /* fall through */
  }
  return "unknown";
}

export function createSkillManifest(installed, targetDir) {
  const manifest = {
    name: "master-trading-skills",
    version: readPackageVersion(),
    installedAt: new Date().toISOString(),
    skills: installed.map((i) => ({
      id: i.skill.id,
      name: i.skill.name,
      path: relative(targetDir, i.dest),
      method: i.method,
    })),
  };

  const manifestPath = join(targetDir, "master-trading-manifest.json");
  return { manifest, manifestPath };
}
