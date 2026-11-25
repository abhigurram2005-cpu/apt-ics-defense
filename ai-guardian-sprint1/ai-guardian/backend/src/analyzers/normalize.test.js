import { test } from "node:test";
import assert from "node:assert/strict";
import {
  inferCategory,
  eslintSeverityToContract,
  semgrepLevelToContract,
  toFinding,
  dedupeFindings
} from "./normalize.js";

test("inferCategory maps security rule ids from either tool", () => {
  assert.equal(inferCategory("javascript.lang.security.audit.insecure-url"), "security");
  assert.equal(inferCategory("generic.sqli-injection"), "security");
  assert.equal(inferCategory("security/detect-child-process"), "security");
});

test("inferCategory detects performance rules", () => {
  assert.equal(inferCategory("python.performance.nplusone-query"), "performance");
});

test("inferCategory defaults everything else to quality", () => {
  assert.equal(inferCategory("no-unused-vars"), "quality");
  assert.equal(inferCategory(undefined), "quality");
});

test("eslint numeric severities map to contract severities", () => {
  assert.equal(eslintSeverityToContract(2), "high");
  assert.equal(eslintSeverityToContract(1), "medium");
  assert.equal(eslintSeverityToContract(0), "low");
  assert.equal(eslintSeverityToContract(undefined), "low");
});

test("semgrep levels map to contract severities", () => {
  assert.equal(semgrepLevelToContract("ERROR"), "high");
  assert.equal(semgrepLevelToContract("WARNING"), "medium");
  assert.equal(semgrepLevelToContract("INFO"), "low");
  assert.equal(semgrepLevelToContract(undefined), "low");
});

test("toFinding clamps invalid lines to 1 and fills missing ruleId", () => {
  const f = toFinding({
    source: "eslint",
    ruleId: "",
    message: "boom",
    file: "a.js",
    line: 0,
    severity: "high"
  });
  assert.equal(f.line, 1);
  assert.equal(f.ruleId, "eslint/unknown");
  assert.equal(f.message, "boom");
  assert.ok(f.id);
});

test("dedupeFindings drops exact rule+file+line duplicates", () => {
  const a = toFinding({ source: "eslint", ruleId: "r1", message: "m", file: "f.js", line: 3, severity: "low" });
  const dup = toFinding({ source: "eslint", ruleId: "r1", message: "m again", file: "f.js", line: 3, severity: "low" });
  const other = toFinding({ source: "eslint", ruleId: "r1", message: "m", file: "f.js", line: 9, severity: "low" });
  const out = dedupeFindings([a, dup, other]);
  assert.equal(out.length, 2);
});
