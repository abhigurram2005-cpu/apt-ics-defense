import { randomUUID } from "crypto";
import { runAnalyzers } from "../analyzers/index.js";

// Sprint 2: real ESLint + Semgrep output, normalized to API_CONTRACT.md.
export async function analyzeCode(req, res) {
  const { projectId, filePath, code } = req.body;

  if (!projectId || !filePath || typeof code !== "string") {
    return res.status(400).json({
      error: "projectId, filePath, and code (string) are required"
    });
  }

  try {
    const analysisId = randomUUID();
    const findings = await runAnalyzers(code, filePath);
    res.json({ analysisId, findings });
  } catch (err) {
    console.error("[analyze] failed:", err);
    res.status(500).json({ error: "Analysis failed" });
  }
}

// Sprint 3 (Member B): replace this stub once the reasoning layer is wired up.
export async function explainFindings(req, res) {
  const { analysisId, findingIds } = req.body;

  if (!analysisId || !Array.isArray(findingIds)) {
    return res.status(400).json({
      error: "analysisId and findingIds (array) are required"
    });
  }

  const explanations = findingIds.map((findingId) => ({
    findingId,
    explanation: "Placeholder explanation — Member B wires this to the LLM in Sprint 3.",
    impact: "Placeholder impact.",
    recommendation: "Placeholder recommendation.",
    alternatives: []
  }));

  res.json({ explanations });
}
