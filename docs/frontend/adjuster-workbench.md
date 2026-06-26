# Adjuster Workbench Frontend

Phase 9 adds the InsureFlow AI adjuster workbench under `frontend`.

The app is a Vue 3/Vite/TypeScript frontend that opens directly to a usable claim queue and selected claim workspace. It uses local demo data first so the portfolio story is visible even when backend and AI services are not running.

## Local Run

```bash
cd frontend
npm install
npm test -- --run
npm run build
npm run dev
```

## First Screen

The first screen is the workbench itself:

- claim queue
- selected claim detail
- customer and policy context
- coverage status
- AI triage
- document intelligence
- RAG assistant
- timeline
- audit view
- human review modal

This is intentionally not a landing page. It is an operational adjuster interface for scanning and reviewing claim intelligence.

## Demo Scenario

The default selected claim is `CLM-20260626-000418`, a high-priority motor collision claim.

The demo shows:

- active motor policy and collision coverage context
- missing police report
- high severity and medium fraud risk
- document intelligence highlights
- RAG answer with policy source reference
- timeline events from backend and AI services
- audit entries
- human review action capture

## Design Boundary

Phase 9 is demo-data-first. It mirrors current backend and AI contracts but does not call them directly yet.

Future frontend phases can add:

- backend API adapters
- authentication
- persisted review actions
- document upload
- live RAG question input
- production routing

## Verification

```bash
cd frontend
npm test -- --run
npm run build
```

The root `./scripts/run-tests.sh` also runs frontend tests and build when `frontend/package.json` exists.
