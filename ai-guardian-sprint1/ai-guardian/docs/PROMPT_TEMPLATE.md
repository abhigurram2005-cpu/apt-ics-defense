# Explain-Finding Prompt Template v1

Target provider: **OpenAI** (`gpt-4o-mini` initially — cheap, supports JSON mode).
Wired up in Sprint 3; drafted in Sprint 2 so schema questions get settled early.

## Request shape (per finding)

One call per finding. `code` = full submitted file; `contextFiles` = related files when available
(Sprint 4 improves this — generic explanations usually mean too little context was sent).

```json
{
  "model": "gpt-4o-mini",
  "response_format": { "type": "json_object" },
  "temperature": 0.2,
  "messages": [
    { "role": "system", "content": "<SYSTEM_PROMPT>" },
    {
      "role": "user",
      "content": "FINDING:\n<ruleId>, <category>, <severity>\n<message>\nLine: <line>\n\nFILE (<filePath>):\n```\n<code>\n```\n\nRELATED FILES:\n<path>: ```\n<code>\n```"
    }
  ]
}
```

## SYSTEM_PROMPT

```
You are a senior code reviewer for an AI-assisted coding tool ("vibe coding").
You receive one static-analysis finding plus the code that triggered it.
Explain it for a developer who may be moving fast and relying on AI-generated code.

Rules:
- Be specific. Reference actual identifiers, values, and line numbers from the code.
- Never invent issues beyond the given finding.
- If context is insufficient to judge impact, say exactly what is missing.
- Respond ONLY with JSON matching:
{
  "explanation": "why this matters, in plain language",
  "impact": "what could break or be exploited, referencing this code specifically",
  "recommendation": "concrete fix, ideally with a short corrected snippet",
  "alternatives": [{ "approach": "...", "tradeoffs": "..." }]
}
"alternatives" may be empty. Max 150 words total.
```

## Response handling

- Parse with `JSON.parse`; on failure retry once at temperature 0, then surface a fallback message.
- Store output on the Finding document (`explanation`, `impact`, `recommendation`, `alternatives`
  fields already exist in `models/Finding.js`).

## Cost controls (build into Sprint 3, not later)

- Cache by hash(`ruleId + file + line + code`) so identical findings never re-trigger a call.
- One finding per call keeps prompts small; batch only if latency demands it.
