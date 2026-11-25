import { runEslint } from "./eslintAnalyzer.js";
import { runSemgrep } from "./semgrepAnalyzer.js";
import { dedupeFindings } from "./normalize.js";

// Runs every analyzer against one file and merges results into the
// contract finding shape. Semgrep failures degrade to ESLint-only.
export async function runAnalyzers(code, filePath) {
  const [eslintFindings, semgrepFindings] = await Promise.all([
    runEslint(code, filePath),
    runSemgrep(code, filePath)
  ]);
  return dedupeFindings([...eslintFindings, ...semgrepFindings]);
}
