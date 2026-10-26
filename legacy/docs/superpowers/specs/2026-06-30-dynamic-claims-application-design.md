# Dynamic Claims Application Design

## Purpose

After Phase 14, InsureFlow AI is a strong portfolio demo with a single-page frontend and rich backend/AI services. The next product step is to turn the frontend into a dynamic multi-page claims application connected to live APIs.

This design covers the roadmap and boundaries for that evolution. Detailed implementation plans should be created phase by phase before code changes begin.

## Current Boundary

The current frontend is intentionally demo-data-first:

- `frontend/src/App.vue` composes the whole workbench.
- `frontend/src/demoData.ts` supplies the visible claims.
- Existing Vue components are useful and should be preserved.
- There is no frontend router, API client layer, auth UI, or live backend data binding.

The backend already provides real service boundaries for claims, policies, documents, triage, human review, governance, audit, security, and integration APIs.

## Architecture Direction

Use a routed Vue application with a small frontend data-access layer.

The frontend should call the Spring Boot backend, not the Python AI services directly. The backend remains the system boundary for authentication, authorization, audit, persistence, and AI orchestration. This keeps the responsible AI story clean: AI output is snapshotted or persisted before the UI presents it as decision support.

## Page Model

The target application should introduce these pages:

- Claim Queue: `/claims`
- Claim Detail: `/claims/:claimNumber`
- Human Review: `/claims/:claimNumber/review`
- Documents: `/documents`, with claim-linked document detail later if needed
- Governance: `/governance`
- Integrations: `/integrations`
- Settings: `/settings`

The app can start by redirecting `/` to `/claims`.

## Phase Breakdown

The recommended next work is six phases:

1. Phase 15: Frontend App Shell And Routing
2. Phase 16: API Client And Live Claim Queue
3. Phase 17: Human Review Workflow
4. Phase 18: Document And RAG Workspace
5. Phase 19: Governance And Audit Dashboards
6. Phase 20: Product Hardening And Demo Readiness

Each phase should be small enough to ship as a reviewed pull request.

## Component Strategy

Reuse the existing workbench widgets instead of rebuilding them:

- `ClaimQueue.vue` becomes the main content for `/claims`.
- `ClaimOverview.vue`, `DocumentPanel.vue`, `TimelinePanel.vue`, `AuditPanel.vue`, `TriagePanel.vue`, and `RagAssistant.vue` remain claim detail widgets.
- `HumanReviewModal.vue` can evolve into a route-backed review form or stay as a modal launched from the review route.

New page-level files should compose these widgets and own route-specific loading/error states.

## Data Strategy

Introduce a clear data mode:

- `demo`: use local data for portfolio screenshots and offline demos.
- `live`: call backend APIs.

The UI should preserve demo mode while live mode grows. This avoids breaking the portfolio experience while new API integration is added.

## Error Handling

Each live page should include:

- loading state
- empty state
- retryable error state
- authorization error state where relevant
- clear display when AI output is unavailable

AI recommendations must remain labeled as recommendations, not final decisions.

## Testing Strategy

Add tests incrementally:

- Phase 15: route rendering and navigation tests.
- Phase 16: API client, DTO mapping, loading/error/empty states.
- Phase 17: human review form validation and submission.
- Phase 18: document/RAG interaction states.
- Phase 19: governance/audit table and filtering behavior.
- Phase 20: browser smoke tests for the end-to-end demo path.

## Documentation Strategy

Use the same documentation-first workflow as earlier phases:

1. Write a phase-specific design spec.
2. Write a phase-specific implementation plan.
3. Implement on a readable feature branch.
4. Update `PROJECT_MEMORY.md`.
5. Open a pull request for review.

The high-level roadmap is documented in `docs/product/dynamic-claims-application-roadmap.md`.

## Recommended First Phase

Start with Phase 15: Frontend App Shell And Routing.

This is the cleanest first step because it creates page boundaries before live API state is introduced. Once pages exist, the claim queue and claim detail pages can be connected to backend APIs without turning the current single `App.vue` file into a large mixed responsibility component.
