# AI Guardian for Vibe Coding — Project Plan

## Team

| Member | Pillar | Owns |
|---|---|---|
| A | Backend & Core Analysis Engine | Express API, DB schema, ESLint/Semgrep/dependency-scanner integration, output schema |
| B | AI Reasoning & Architecture/Impact | Prompt design, LLM integration, import-graph architecture rule, change-impact analysis |
| C | Dashboard Frontend | React/TS/Tailwind UI, health score & issue visualizations, auth |
| D | Extension, Integration & DevOps | VS Code extension, GitHub Action (PR trigger), Docker/CI, deployment |

## Scope decisions

**In scope (MVP + production):** security analysis, code quality analysis, dependency analysis (npm audit wrapper), one showcase architecture rule (via import graph, not general architecture inference), change-impact summary, AI reasoning/explanation layer, alternative-solution comparison, project health dashboard, VS Code extension (on-save), GitHub Action (on-PR).

**Explicitly future work (state this in the report, don't attempt):** multi-language support, general-purpose architecture inference, embeddings/RAG over the full codebase (use import-graph context instead), historical trend analytics beyond before/after score, CI providers beyond GitHub.

## Sprint plan (2-week sprints, weeks 1–24)

### Sprint 1 (Wk 1–2) — Foundations
All: SRS/design doc, repo + project board, API contract v1.
A: Express skeleton, Mongo schema draft, Dockerfile.
B: LLM API research (cost/rate limits), draft prompt template structure.
C: React/TS/Tailwind scaffold, wireframes, auth flow design.
D: VS Code Extension API + GitHub Actions research, basic CI.

### Sprint 2 (Wk 3–4) — Static analysis core
A: integrate ESLint + Semgrep, define analysis-output JSON schema.
B: first prompt template — one static finding + code → explanation.
C: static dashboard components (health score card, issue list) vs mock data.
D: minimal extension — reads active file, POSTs to mock endpoint.
**Deliverable:** backend runs ESLint/Semgrep on a sample file, returns structured JSON.

### Sprint 3 (Wk 5–6) — First real pipeline
A: wire findings through API, persist to MongoDB.
B: connect reasoning layer to real findings, save explanation + recommendation.
C: dashboard reads real backend data for one seeded repo.
D: extension calls real backend, shows raw JSON in output panel.
**Internal demo:** AI-generated diff → static analysis → AI explanation, end to end (security + code quality only).

### Sprint 4 (Wk 7–8) — Dependencies + real UX
A: dependency analysis (npm audit wrapper).
B: richer prompt context (surrounding file, related utilities); start alternative-solution logic.
C: issue detail view, health score broken down by category.
D: inline diagnostics/squiggles in the extension.

### Sprint 5 (Wk 9–10) — Architecture + impact (highest-risk sprint — pair A+B)
A: import/dependency graph (madge / dependency-cruiser).
B: one showcase architecture rule on that graph, plus change-impact summaries.
C: architecture-violations panel, "affected files" view.
D: debounce on-save triggering; start GitHub Action skeleton.

### Sprint 6 (Wk 11–12) — MVP integration + mid-term review
All: bug bash against 2–3 realistic sample repos.
A/B: caching so identical diffs don't re-hit the LLM.
C: finalize weighted health-score calc, demo polish.
D: GitHub Action posts PR comments; extension stable for live demo.
**🎯 MVP milestone.**

### Sprint 7 (Wk 13–14) — Performance + technical debt
A: performance heuristics (N+1 queries, inefficient loops).
B: technical-debt scoring across commits over time.
C: historical health trend chart.
D: harden extension for large files, error/loading states.

### Sprint 8 (Wk 15–16) — Alternative-solution recommendations
A: "compare two implementations" endpoint.
B: comparison prompt engineering (complexity, performance, security, maintainability).
C: current-vs-alternative comparison UI.
D: JWT auth + optional GitHub OAuth.

### Sprint 9 (Wk 17–18) — DevOps hardening
A: rate limiting, input validation, error handling.
B: sanitize code sent to the LLM (untrusted input), cost/usage logging.
C: responsive + accessibility pass.
D: Dockerize full stack, docker-compose, staging deploy.

### Sprint 10 (Wk 19–20) — Testing
A: unit tests on analysis engine.
B: run reasoning layer against benchmark set, measure precision/recall.
C: E2E tests on critical dashboard flows.
D: CI runs full suite on PR, auto-deploy staging on merge.

### Sprint 11 (Wk 21–22) — Evaluation
All: finish benchmark run (precision/recall/false-positive rate), write up.
All: 5–8 outside users test on a sample repo (~20 min), collect feedback.
Fix what the study surfaces as most confusing/wrong.

### Sprint 12 (Wk 23–24) — Final polish & submission
Bug fixes from user study, performance tuning.
Production deployment + setup docs.
README, architecture diagram, user guide, demo video.
Final report: design, implementation, evaluation, limitations, future work.
**🎯 Final milestone.**

## If something slips
Sprint 5 (architecture/impact graph) is most likely to overrun — it's genuinely novel, not a wrapper around an existing tool. Compress Sprints 7–8 first if needed (performance analysis, alternative-solution comparison — valuable but not load-bearing). Never compress Sprints 10–11 (testing/evaluation) — a project with no evaluation section is weaker than one with fewer features.

## Evaluation methodology
- Benchmark: 20–30 code snippets with seeded issues (OWASP examples, classic N+1 queries, duplicated-validation cases) → measure precision/recall/false-positive rate.
- User study: 5–8 people use the tool on a sample repo for ~20 minutes, short feedback form.
