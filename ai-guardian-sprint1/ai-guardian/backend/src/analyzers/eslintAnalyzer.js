import { Linter } from "eslint";
import js from "@eslint/js";
import { toFinding, eslintSeverityToContract } from "./normalize.js";

const linter = new Linter();

// Fixed config: recommended rules, no project eslintrc lookup. In-memory only.
const config = {
  ...js.configs.recommended,
  languageOptions: {
    ecmaVersion: 2022,
    sourceType: "module",
    globals: {
      console: "readonly",
      process: "readonly",
      window: "readonly",
      document: "readonly",
      fetch: "readonly",
      require: "readonly",
      module: "writable",
      exports: "writable",
      Buffer: "readonly",
      setTimeout: "readonly",
      setInterval: "readonly",
      clearTimeout: "readonly",
      clearInterval: "readonly"
    }
  }
};

export function runEslint(code, filePath) {
  const messages = linter.verify(code, config, filePath);
  return messages.map((msg) =>
    toFinding({
      source: "eslint",
      ruleId: msg.ruleId || (msg.fatal ? "eslint/parse-error" : ""),
      message: msg.message,
      file: filePath,
      line: msg.line,
      severity: eslintSeverityToContract(msg.severity)
    })
  );
}
