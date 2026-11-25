// End-to-end smoke test: POSTs the vulnerable fixture to a running backend
// and prints normalized findings. Usage: start the backend, then `npm run smoke`.
import { readFile } from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

const here = path.dirname(fileURLToPath(import.meta.url));
const code = await readFile(path.join(here, "../../samples/vulnerable-sample.js"), "utf8");

const res = await fetch("http://localhost:4000/api/analyze", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    projectId: "smoke-test",
    filePath: "samples/vulnerable-sample.js",
    code
  })
});

if (!res.ok) {
  console.error(`Request failed: ${res.status} ${await res.text()}`);
  process.exit(1);
}

const { analysisId, findings } = await res.json();
console.log(`analysisId: ${analysisId}\n`);
for (const f of findings) {
  console.log(`${f.severity.padEnd(7)} [${f.category}] ${f.ruleId} @ line ${f.line}`);
}
console.log(`\nTotal: ${findings.length} findings`);
