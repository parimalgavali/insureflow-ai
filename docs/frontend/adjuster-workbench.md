# Adjuster Workbench Frontend

Phase 9 added the InsureFlow AI adjuster workbench under `frontend`.

The app is a Vue 3/Vite/TypeScript frontend. Phase 15 adds Vue Router and turns the original single-page workbench into a routed application shell while keeping local demo data as the active data source.

## Local Run

```bash
cd frontend
npm install
npm test -- --run
npm run build
npm run dev
```

## Routes

The routed demo app currently exposes:

- `/claims` - claim queue
- `/claims/:claimNumber` - claim detail workbench
- `/claims/:claimNumber/review` - human review checkpoint
- `/documents` - document intelligence workspace
- `/governance` - audit and responsible AI evidence
- `/integrations` - Guidewire-inspired integration console placeholder
- `/settings` - demo mode and API connection context

The root route `/` redirects to `/claims`.

## First Screen

The first useful screen is the claim queue. Opening a claim shows the full workbench:

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

The frontend is still demo-data-first. It mirrors current backend and AI contracts but does not call them directly yet.

Future frontend phases can add:

- backend API adapters
- authentication
- persisted review actions
- document upload
- live RAG question input
- live governance/audit filtering

## Verification

```bash
cd frontend
npm test -- --run
npm run build
```

The root `./scripts/run-tests.sh` also runs frontend tests and build when `frontend/package.json` exists.
