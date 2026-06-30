# Dynamic Claims Application Roadmap

This document defines the next product evolution after Phase 14 portfolio packaging.

The current InsureFlow AI frontend is a polished single-page adjuster workbench that uses local demo data. The backend already contains many live insurance APIs for customers, policies, claims, documents, triage, human review, governance, audit, integration events, and security. The next product goal is to turn the demo workbench into a dynamic multi-page claims application connected to those live backend APIs.

## Product Goal

Build a realistic claims operations application where an adjuster can sign in, browse live claims, open claim details, review AI recommendations, submit human review decisions, inspect documents, ask grounded RAG questions, and view audit/governance evidence.

The product should remain portfolio-friendly: every phase must produce something demonstrable, documented, and testable.

## Current State

### What Exists

- Vue 3, Vite, and TypeScript frontend.
- Single-page adjuster workbench in `frontend/src/App.vue`.
- Reusable frontend widgets:
  - claim queue
  - claim overview
  - document intelligence panel
  - AI triage panel
  - RAG assistant panel
  - timeline panel
  - audit panel
  - human review modal
- Local demo data in `frontend/src/demoData.ts`.
- Spring Boot backend APIs for:
  - authentication
  - customers
  - policies
  - coverage validation
  - FNOL and claims
  - claim documents
  - claim notes
  - claim events and timeline
  - AI triage
  - human review
  - audit logs
  - governance model and prompt versions
  - Guidewire-inspired integration APIs
- Python AI services for:
  - triage
  - document intelligence
  - RAG assistant
  - ML model training and inference support

### What Does Not Exist Yet

- Frontend routing.
- Separate claim queue, claim detail, review, governance, document, integration, and admin pages.
- A frontend API client layer.
- Authentication UI and token handling.
- Live frontend calls to the backend.
- Persisted frontend review actions.
- Live document upload or document intelligence execution from the UI.
- Live RAG question input from the UI.
- Frontend error/loading/empty states for network-backed workflows.

## Recommended Phase Model

The dynamic product should be built in six new phases.

| Phase | Name | Outcome |
| --- | --- | --- |
| Phase 15 | Frontend App Shell And Routing | Multi-page frontend structure exists, still mostly demo-data-backed. |
| Phase 16 | API Client And Live Claim Queue | Claim list and claim detail read from the backend. |
| Phase 17 | Human Review Workflow | Adjuster decisions are submitted to the backend and reflected in the UI. |
| Phase 18 | Document And RAG Workspace | Document status, summaries, and RAG questions become interactive/live. |
| Phase 19 | Governance And Audit Dashboards | Audit logs, model versions, prompt versions, and AI evidence become browsable. |
| Phase 20 | Product Hardening And Demo Readiness | UX polish, error handling, integration tests, seed data, and demo runbooks are production-shaped. |

This sequence is intentionally frontend-first but contract-aware. It avoids rebuilding backend behavior that already exists, while adding backend endpoints only where the UI exposes a real gap.

## Phase 15: Frontend App Shell And Routing

### Goal

Create the multi-page frontend foundation without changing backend behavior.

### Build

- Add Vue Router.
- Replace the single `App.vue` workbench composition with a routed application shell.
- Add persistent layout:
  - top navigation
  - sidebar or section navigation
  - signed-in adjuster identity placeholder
  - active claim context when applicable
- Create initial pages:
  - `/claims`
  - `/claims/:claimNumber`
  - `/claims/:claimNumber/review`
  - `/documents`
  - `/governance`
  - `/integrations`
  - `/settings`
- Move current workbench widgets into page-level layouts.
- Keep demo data active during this phase.

### Success Criteria

- User can navigate between pages.
- Claim queue page opens as the first useful screen.
- Claim detail page shows the existing workbench widgets for a selected claim.
- Existing frontend tests pass.
- New router tests cover the main routes.

### Branch Name

`frontend-routing-shell`

## Phase 16: API Client And Live Claim Queue

### Goal

Connect the claim queue and claim detail page to live backend APIs.

### Build

- Add typed frontend API client.
- Add runtime API base URL configuration.
- Add claim list loading from backend.
- Add claim detail loading from backend.
- Map backend claim DTOs into frontend view models.
- Preserve demo fallback only for local/demo mode.
- Add loading, error, and empty states.
- Add API contract tests/mocks.

### Backend Gaps To Check

- Does the backend expose a claim list endpoint with enough queue metadata?
- Does the claim detail response include all UI fields, or should the frontend compose multiple backend calls?
- Does the backend expose latest AI triage result and timeline in a frontend-friendly way?

### Success Criteria

- Frontend can display real backend claim data.
- Demo mode can still run without backend for portfolio screenshots.
- API failures produce useful user-facing states.
- Claim selection changes the route and reloads data.

### Branch Name

`live-claim-queue`

## Phase 17: Human Review Workflow

### Goal

Make human review actions real and persisted.

### Build

- Connect the human review page/modal to backend human review APIs.
- Add review decision form states:
  - approve
  - request information
  - escalate
  - reject or hold, if supported by the backend contract
- Show submitted review decision history.
- Reflect review actions in claim timeline/audit views.
- Add role-aware UI behavior for adjuster and senior adjuster users.

### Backend Gaps To Check

- Does the human review API return enough display history?
- Should claim status change automatically after review, or should review and status transition stay separate?
- Are reason codes and allowed decision values aligned between frontend and backend?

### Success Criteria

- User can submit a review decision from the UI.
- Refreshing the page keeps the decision visible.
- Claim timeline/audit reflects the review event.
- High-priority claims continue to require human review before workflow movement.

### Branch Name

`human-review-workflow`

## Phase 18: Document And RAG Workspace

### Goal

Turn document intelligence and grounded Q&A into interactive workspaces.

### Build

- Add document page for a claim.
- Display received and missing documents from backend metadata.
- Add document upload or document registration flow, depending on backend support.
- Trigger or display document intelligence summaries.
- Add RAG question input.
- Show grounded RAG answer, confidence/coverage state, and source references.
- Add missing-evidence and no-answer states.

### Backend Gaps To Check

- Does the backend orchestrate document intelligence and RAG calls, or should the frontend call AI services only through the backend?
- Is file upload in scope, or should documents remain metadata-only for the first version?
- Where should RAG answer audit events be stored?

### Success Criteria

- User can inspect documents separately from the claim overview.
- User can ask a claim/policy question and receive a sourced answer.
- Missing source evidence is visible and not hidden.
- AI outputs remain clearly labeled as decision support.

### Branch Name

`document-rag-workspace`

## Phase 19: Governance And Audit Dashboards

### Goal

Expose responsible AI and operational audit evidence through real UI pages.

### Build

- Add governance dashboard.
- Show model versions.
- Show prompt versions.
- Show audit logs with filters:
  - claim number
  - actor
  - event type
  - date/time
  - correlation ID
- Add AI decision evidence view:
  - triage score
  - reason codes
  - model/rule version
  - RAG sources
  - human override status
- Add integration event viewer for Guidewire-inspired sync events.

### Backend Gaps To Check

- Does the audit log API support filtering and pagination?
- Does governance expose enough model/prompt metadata for UI display?
- Does the integration event endpoint expose event details safely?

### Success Criteria

- A reviewer can trace how an AI-assisted claim decision was produced.
- Governance pages are understandable to both technical and non-technical evaluators.
- Audit pages support at least basic filtering.
- No sensitive token or secret data is shown.

### Branch Name

`governance-audit-dashboard`

## Phase 20: Product Hardening And Demo Readiness

### Goal

Make the dynamic app reliable, explainable, and easy to run.

### Build

- Add seeded demo dataset for end-to-end UI walkthroughs.
- Add Playwright or equivalent browser smoke tests.
- Add API mock mode for frontend CI.
- Improve responsive layout across laptop and tablet widths.
- Add consistent loading/error/empty states across all pages.
- Update Docker Compose app profile if needed.
- Update README, demo script, screenshots checklist, and recruiter walkthrough.

### Success Criteria

- A fresh environment can run the full app with one documented command sequence.
- Main user journeys are covered by automated tests:
  - view claim queue
  - open claim detail
  - submit human review
  - ask RAG question
  - inspect governance/audit evidence
- Demo docs match the real UI.
- CI remains green.

### Branch Name

`dynamic-app-hardening`

## Target Page Map

| Page | Route | Purpose | Data Source |
| --- | --- | --- | --- |
| Claim Queue | `/claims` | Browse and filter open work. | Backend claims API |
| Claim Detail | `/claims/:claimNumber` | View claim, policy, triage, timeline, documents, RAG summary. | Backend claims, policy, triage, document, RAG APIs |
| Human Review | `/claims/:claimNumber/review` | Record adjuster decision and reason. | Backend human review API |
| Documents | `/documents` and claim-linked document views | Inspect document status and document intelligence output. | Backend document metadata and document AI orchestration |
| Governance | `/governance` | View model/prompt versions and responsible AI evidence. | Backend governance API |
| Audit | Could be part of `/governance` first | Trace claim and AI actions. | Backend audit API |
| Integrations | `/integrations` | Inspect Guidewire-inspired event syncs. | Backend integration API |
| Settings | `/settings` | Environment, demo mode, and user preferences. | Frontend config first, backend later if needed |

## Data Flow

The frontend should not call Python AI services directly in the productized app.

Recommended flow:

1. Frontend calls Spring Boot backend.
2. Spring Boot handles authentication, authorization, persistence, and audit.
3. Spring Boot calls AI services when needed.
4. AI service responses are stored or snapshotted by the backend.
5. Frontend reads the persisted/snapshotted decision-support output from the backend.

This keeps the audit trail, security, and governance story stronger.

## Demo Mode Strategy

Keep demo mode, but make it explicit.

- `live` mode uses backend APIs.
- `demo` mode uses local sample data.
- The UI should make the active mode clear in development or demo environments.
- Tests should cover both mapping from backend DTOs and demo fallback behavior.

This preserves the portfolio experience while allowing the project to become a real dynamic application.

## Testing Strategy

Each phase should include tests at the right layer.

- Router/page tests for Phase 15.
- API client and mapping tests for Phase 16.
- Form and persistence tests for Phase 17.
- Document/RAG interaction tests for Phase 18.
- Governance/audit filtering tests for Phase 19.
- End-to-end smoke tests for Phase 20.

Backend tests should be added only when new backend behavior or API contract changes are required.

## Documentation Strategy

Each phase should follow the same documentation pattern used in Phases 0-14:

1. Create a design spec in `docs/superpowers/specs/`.
2. Create an implementation plan in `docs/superpowers/plans/`.
3. Update feature-specific docs under `docs/frontend/`, `docs/api/`, or `docs/demo/`.
4. Update `PROJECT_MEMORY.md` after important decisions, branch creation, implementation completion, PR creation, and merge.
5. Keep the root README aligned only after the product behavior is real.

## Recommended Execution Order

Start with Phase 15.

Do not connect the frontend to live APIs before routing and page boundaries exist. If API calls are added while everything remains inside one large page, the frontend will become harder to maintain and harder to explain.

The safest sequence is:

1. Phase 15: create page structure using existing demo data.
2. Phase 16: connect claim queue and claim detail to the backend.
3. Phase 17: make the highest-value workflow, human review, persistent.
4. Phase 18: make AI assistance interactive.
5. Phase 19: expose governance and audit.
6. Phase 20: harden the complete product.

## Open Decisions Before Phase 15

- Whether to keep the first screen as `/claims` or `/`.
- Whether the navigation should be a left sidebar, top tabs, or a hybrid layout.
- Whether authentication UI should begin in Phase 15 or wait until after live API integration.
- Whether document upload should be included in Phase 18 or kept as metadata-only first.

## Recommended Answers

- Use `/claims` as the first real page and redirect `/` to `/claims`.
- Use a compact left navigation plus top claim context bar.
- Keep authentication UI minimal until Phase 16 or 17, because API connection will clarify token handling.
- Keep Phase 18 metadata-first unless file upload is needed for the demo story.
