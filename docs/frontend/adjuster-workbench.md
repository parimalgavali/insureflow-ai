# Adjuster Workbench Frontend

Phase 9 added the InsureFlow AI adjuster workbench under `frontend`.

The app is a Vue 3/Vite/TypeScript frontend. Phase 15 added Vue Router and turned the original single-page workbench into a routed application shell. Phase 16 adds a typed claim API client and live claim queue/detail wiring while keeping demo mode available.

## Local Run

```bash
cd frontend
npm install
npm test -- --run
npm run build
npm run dev
```

By default, the frontend runs in demo mode so the portfolio workflow is visible without a backend. To run the queue and claim detail pages against the Spring Boot backend:

```bash
VITE_DATA_MODE=live npm run dev
```

In Vite dev mode, `/api` proxies to `http://localhost:8080`. In Docker Compose, nginx proxies `/api` to the `api` service.

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

## Data Modes

- `demo` uses `frontend/src/demoData.ts`.
- `live` calls `/api/v1/claims`, `/api/v1/claims/{claimNumber}`, `/api/v1/claims/{claimNumber}/events`, and `/api/v1/claims/{claimNumber}/triage`.
- Live mode bootstraps a development adjuster token through `/api/v1/auth/dev-token`.

## Design Boundary

Claim queue and claim detail data can now come from the backend. Rich document intelligence and RAG interaction are still represented with placeholders in live mode until Phase 18.

Future frontend phases can add:

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
