import { randomUUID } from "crypto";

// Single source of truth for mapping raw analyzer output onto the
// category/severity enums locked in docs/API_CONTRACT.md. All pure functions.

const CATEGORY_MATCHERS = [
  ["security", "security"],
  ["injection", "security"],
  ["xss", "security"],
  ["sqli", "security"],
  ["owasp", "security"],
  ["nplusone", "performance"]
];

export function inferCategory(ruleId) {
  const id = String(ruleId ?? "").toLowerCase();
  for (const [needle, category] of CATEGORY_MATCHERS) {
    if (id.includes(needle)) return category;
  }
  return "quality";
}

export function eslintSeverityToContract(severity) {
  if (severity === 2) return "high";
  if (severity === 1) return "medium";
  return "low";
}

export function semgrepLevelToContract(level) {
  switch (String(level ?? "").toUpperCase()) {
    case "ERROR":
      return "high";
    case "WARNING":
      return "medium";
    default:
      return "low";
  }
}

export function toFinding({ source, ruleId, message, file, line, severity }) {
  const lineNum = Number(line);
  return {
    id: randomUUID(),
    category: inferCategory(ruleId),
    severity,
    ruleId: ruleId || `${source}/unknown`,
    message: String(message),
    file,
    line: Number.isFinite(lineNum) && lineNum > 0 ? lineNum : 1
  };
}

export function dedupeFindings(findings) {
  const seen = new Set();
  const out = [];
  for (const finding of findings) {
    const key = `${finding.ruleId}|${finding.file}|${finding.line}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(finding);
  }
  return out;
}
