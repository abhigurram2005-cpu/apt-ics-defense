import { test } from "node:test";
import assert from "node:assert/strict";
import { runEslint } from "./eslintAnalyzer.js";

test("runEslint maps recommended-rule errors to high quality findings", () => {
  const findings = runEslint("const x = 1;\nconsole.log('hi');\n", "src/sample.js");
  const unused = findings.find((f) => f.ruleId === "no-unused-vars");
  assert.ok(unused, "expected a no-unused-vars finding");
  assert.equal(unused.category, "quality");
  assert.equal(unused.severity, "high");
  assert.equal(unused.file, "src/sample.js");
});

test("runEslint reports parse errors instead of throwing", () => {
  const findings = runEslint("function {{{{", "src/broken.js");
  assert.ok(findings.some((f) => f.ruleId === "eslint/parse-error"));
});

test("runEslint returns nothing for clean code", () => {
  const findings = runEslint("export const add = (a, b) => a + b;\n", "src/add.js");
  assert.deepEqual(findings, []);
});
