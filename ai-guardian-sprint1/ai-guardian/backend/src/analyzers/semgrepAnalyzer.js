import { execFile } from "child_process";
import { mkdtemp, writeFile, rm } from "fs/promises";
import { tmpdir } from "os";
import path from "path";
import { toFinding, semgrepLevelToContract } from "./normalize.js";

const TIMEOUT_MS = 20000;
let warned = false;

function tempFileName(filePath) {
  // Safe basename + real extension so semgrep picks the right language.
  const base = path.basename(filePath).replace(/[^\w.-]/g, "_");
  return /\.(js|mjs|cjs|ts|jsx|tsx)$/.test(base) ? base : `${base}.js`;
}

// Shells out to semgrep. Graceful degradation: if the binary is missing
// (no native Windows build) or fails, return [] and warn once — analysis
// must never fail because of semgrep.
export async function runSemgrep(code, filePath) {
  const dir = await mkdtemp(path.join(tmpdir(), "ai-guardian-"));
  const file = path.join(dir, tempFileName(filePath));
  try {
    await writeFile(file, code, "utf8");
    const stdout = await new Promise((resolve, reject) => {
      execFile(
        "semgrep",
        ["scan", "--json", "--quiet", "--config", "auto", file],
        { timeout: TIMEOUT_MS, maxBuffer: 10 * 1024 * 1024 },
        (err, stdout, stderr) => {
          if (err && !stdout) {
            err.stderr = stderr;
            reject(err);
          } else {
            resolve(stdout);
          }
        }
      );
    });

    return (JSON.parse(stdout).results ?? []).map((r) =>
      toFinding({
        source: "semgrep",
        ruleId: r.check_id,
        message: r.extra?.message ?? r.check_id,
        file: filePath,
        line: r.start?.line,
        severity: semgrepLevelToContract(r.extra?.severity)
      })
    );
  } catch (err) {
    if (!warned) {
      warned = true;
      console.warn(`[semgrep] skipping (${err.code === "ENOENT" ? "binary not found on this machine" : err.message})`);
    }
    return [];
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}
