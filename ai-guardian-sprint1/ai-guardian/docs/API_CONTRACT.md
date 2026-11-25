# API Contract v1 (draft — lock this in Sprint 1)

Base URL: `http://localhost:4000/api`

## POST /analyze
Triggered by the VS Code extension (on save) or the GitHub Action (on PR).

**Request**
```json
{
  "projectId": "string",
  "filePath": "src/routes/auth.js",
  "code": "string (full file content)",
  "diff": "string (unified diff, optional)",
  "context": {
    "language": "javascript",
    "relatedFiles": [
      { "path": "src/utils/validate.js", "code": "string" }
    ]
  }
}
```

**Response**
```json
{
  "analysisId": "string",
  "findings": [
    {
      "id": "string",
      "category": "security | quality | performance | architecture | dependency",
      "severity": "critical | high | medium | low",
      "ruleId": "string (e.g. semgrep rule id or eslint rule)",
      "message": "string (raw finding, pre-AI)",
      "file": "src/routes/auth.js",
      "line": 42
    }
  ]
}
```

## POST /explain
Sends raw findings + surrounding context to the AI reasoning layer.

**Request**
```json
{
  "analysisId": "string",
  "findingIds": ["string"]
}
```

**Response**
```json
{
  "explanations": [
    {
      "findingId": "string",
      "explanation": "string (why this matters, in plain language)",
      "impact": "string (what else this could affect)",
      "recommendation": "string (suggested fix)",
      "alternatives": [
        { "approach": "string", "tradeoffs": "string" }
      ]
    }
  ]
}
```

## GET /projects/:id/health
Used by the dashboard.

**Response**
```json
{
  "projectId": "string",
  "overallScore": 84,
  "categoryScores": {
    "security": 78,
    "quality": 89,
    "performance": 91,
    "architecture": 82
  },
  "history": [
    { "date": "2026-08-01", "score": 88 },
    { "date": "2026-08-10", "score": 84 }
  ]
}
```

## GET /projects/:id/issues
**Response**
```json
{
  "issues": [
    {
      "id": "string",
      "file": "string",
      "line": 42,
      "category": "security",
      "severity": "high",
      "message": "string",
      "explanation": "string",
      "recommendation": "string",
      "status": "open | acknowledged | resolved"
    }
  ]
}
```

## Notes for all members
- `category` and `severity` enums above are the single source of truth — don't invent new values without updating this doc.
- The extension and GitHub Action both hit `/analyze` then `/explain` — same contract, two trigger surfaces.
- Any schema change goes through a PR to this file first, not silently in code.
