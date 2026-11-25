# AI Guardian for Vibe Coding

Quality-control layer for AI-assisted coding. See `docs/PROJECT_PLAN.md` for the full 24-week sprint plan and `docs/API_CONTRACT.md` for the locked request/response schemas.

## Structure

```
ai-guardian/
├── docs/               PROJECT_PLAN.md, API_CONTRACT.md
├── backend/            Express + MongoDB analysis API      (Member A)
├── dashboard/          React + TS + Tailwind dashboard      (Member C)
├── extension/          VS Code extension                    (Member D)
└── .github/workflows/  CI                                    (Member D)
```

## Local setup

**Backend**
```
cd backend
cp .env.example .env
npm install
npm run dev
```

**Dashboard**
```
cd dashboard
npm install
npm run dev
```

**Full stack via Docker (backend + Mongo)**
```
docker compose up
```

**Extension**
Open `extension/` in VS Code, press F5 to launch an Extension Development Host, then run the "AI Guardian: Analyze current file" command (requires the backend running locally).

## Sprint 1 status
- [x] Repo structure + API contract v1
- [x] Backend skeleton (Express, Mongo models, stub `/analyze` and `/explain`)
- [x] Dashboard skeleton (health card + issue list against mock data)
- [x] Extension skeleton (command-triggered, hits local backend)
- [x] CI workflow (install + build/test on push)
- [ ] Member B: LLM API research + first prompt template (Sprint 2 deliverable)

## Next up: Sprint 2
Replace the stub finding in `backend/src/controllers/analysisController.js` with real ESLint + Semgrep output. See `docs/PROJECT_PLAN.md` for the full breakdown.
