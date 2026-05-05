/**
 * Minimal Interactive Prompts (Node.js built-in only)
 */

import { createInterface } from "readline";

const rl = createInterface({
  input: process.stdin,
  output: process.stdout,
});

export function ask(question) {
  return new Promise((resolve) => {
    rl.question(question, (answer) => resolve(answer.trim()));
  });
}

export async function askChoice(question, options) {
  console.log(`\n${question}`);
  options.forEach((opt, i) => {
    console.log(`  ${i + 1}. ${opt.label}${opt.recommended ? " (Recommended)" : ""}`);
  });

  while (true) {
    const answer = await ask("Select (number): ");
    const idx = parseInt(answer, 10) - 1;
    if (idx >= 0 && idx < options.length) {
      return options[idx].value;
    }
    console.log("Invalid selection. Please try again.");
  }
}

export async function askMultiSelect(question, options) {
  console.log(`\n${question}`);
  console.log("Space-separated numbers to select multiple, or 'all'");
  options.forEach((opt, i) => {
    const mark = opt.required ? " [REQUIRED]" : "";
    console.log(`  ${i + 1}. ${opt.label}${mark}`);
    console.log(`     ${opt.description}`);
  });

  while (true) {
    const answer = await ask("Select: ");
    if (answer.toLowerCase() === "all") {
      return options.filter((o) => !o.isMeta).map((o) => o.value);
    }

    const indices = answer
      .split(/\s+/)
      .map((n) => parseInt(n, 10) - 1)
      .filter((n) => n >= 0 && n < options.length);

    if (indices.length > 0) {
      return indices.map((i) => options[i].value);
    }
    console.log("Invalid selection. Please try again.");
  }
}

export function closePrompt() {
  rl.close();
}
