# Adjuster Workbench Frontend

Phase 9 added the InsureFlow AI adjuster workbench under `frontend`.

The app is a Vue 3/Vite/TypeScript frontend. Phase 15 added Vue Router and turned the original single-page workbench into a routed application shell. Phase 16 added a typed claim API client and live claim queue/detail wiring while keeping demo mode available. Phase 18 connects the documents workspace to live document and RAG decision-support APIs. Phase 19 turns governance into a live/demo dashboard for model versions, prompt versions, audit events, and AI evidence.

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

Live human review submission also requires an adjuster UUID that exists in the backend:

```bash
VITE_DATA_MODE=live VITE_REVIEWER_ADJUSTER_ID=<adjuster-uuid> npm run dev
```

## Routes

The routed demo app currently exposes:

- `/claims` - claim queue
- `/claims/:claimNumber` - claim detail workbench
- `/claims/:claimNumber/review` - human review checkpoint and review history
- `/documents` - interactive document intelligence and grounded Q&A workspace
- `/governance` - governance dashboard with model registry, prompt registry, audit events, and AI evidence
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
- `live` calls `/api/v1/claims`, `/api/v1/claims/{claimNumber}`, `/api/v1/claims/{claimNumber}/events`, `/api/v1/claims/{claimNumber}/triage`, `/api/v1/claims/{claimNumber}/human-reviews`, `/api/v1/claims/{claimNumber}/document-workspace`, `/api/v1/claims/{claimNumber}/rag-query`, `/api/v1/governance/model-versions`, `/api/v1/governance/prompt-versions`, and `/api/v1/audit/events`.
- Live mode bootstraps a development adjuster token through `/api/v1/auth/dev-token`.

## Document And RAG Workspace

The `/documents` route now loads claims through the repository layer, lets the adjuster select a claim, displays received and missing document status, and submits grounded questions through the same repository abstraction. Demo mode reuses `frontend/src/demoData.ts`; live mode calls the Spring Boot facade so authentication, persistence, and audit stay backend-owned.

Claim detail pages also enrich live claims with document workspace output and a default RAG answer.

## Governance Dashboard

The `/governance` route shows:

- model versions and active status
- prompt versions and model bindings
- audit events with actor, entity, status, and correlation ID
- AI evidence cards with triage labels, reason codes, queue recommendation, human-review flag, and RAG source count

Demo mode derives this from `frontend/src/demoData.ts`. Live mode calls the Spring Boot governance and audit APIs through the repository layer.

## Demo Readiness

Phase 20 adds a readiness panel on `/settings` with:

- current data mode
- `/api` proxy context
- frontend smoke coverage
- Docker app-profile validation command
- live backend mode hint using `VITE_DATA_MODE=live`

Before a recruiter or interview demo, run:

```bash
./scripts/demo-readiness-check.sh
```

## Design Boundary

Claim queue, claim detail, human review, document workspace, RAG question submission, and governance/audit dashboard data can now come from the backend. File upload, production login UI, and full audit pagination/date-range filtering remain future hardening work.

Future frontend phases can add:

- document upload
- richer audit pagination and date-range filtering

## Verification

```bash
cd frontend
npm test -- --run
npm run build
```

The root `./scripts/run-tests.sh` also runs frontend tests and build when `frontend/package.json` exists.
