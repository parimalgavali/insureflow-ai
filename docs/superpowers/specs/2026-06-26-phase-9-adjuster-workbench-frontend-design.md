# Phase 9 Adjuster Workbench Frontend Design

## Context

Phase 9 introduces the first user-facing application for InsureFlow AI: a Vue adjuster workbench. The backend, triage service, ML training, document intelligence service, and RAG assistant now have stable local contracts. The frontend should make that work visible to recruiters and hiring managers in a realistic claims operations interface.

The workbench must not be a marketing landing page. The first screen should be the actual claim queue and a selected claim workspace. The goal is to make the insurance workflow understandable quickly: policy/coverage context, claim facts, AI triage, document intelligence, RAG assistance, timeline, and human review.

## Recommended Approach

I considered three approaches:

1. **Backend-connected app first:** connect directly to the Spring Boot backend and AI services.
   This is realistic but brittle for a portfolio demo because all services must be running and seeded.

2. **Demo-data-first Vue app:** build a polished Vue/Vite/TypeScript workbench with local typed demo data and a clean API adapter boundary for later backend integration.
   This is the recommended Phase 9 approach. It gives recruiters an immediately usable UI and keeps the future integration path clear.

3. **Static HTML prototype:** build a dependency-free static page.
   This would reduce setup, but it would not satisfy the blueprint’s Vue workbench goal and would be harder to evolve into a real frontend.

Phase 9 will use option 2.

## Scope

Phase 9 includes:

- Vue 3, Vite, TypeScript frontend scaffold under `frontend`.
- First screen as a usable adjuster workbench, not a landing page.
- Claim queue with filters/search and visible risk/status signals.
- Claim detail workspace for the selected claim.
- Policy and customer context panel.
- AI triage panel with severity, fraud, litigation, recommended queue, reason codes, and human-review flag.
- Document intelligence panel with extraction highlights, missing documents, and summary sections.
- RAG assistant panel with sample questions, grounded answer, and source references.
- Claim timeline.
- Human review/override modal.
- Audit view for AI/RAG/human review events.
- Local demo data and typed frontend domain models.
- Component/unit tests for core behavior.
- Production build verification.

Phase 9 does not include:

- Real authentication.
- Live backend calls by default.
- Upload workflows.
- Editing policies or claims.
- Persisting human overrides.
- Complex charting libraries.

## User Experience

The workbench opens into a dense operational layout:

- A narrow top bar shows the product name, active role, environment label, and current selected claim.
- A left queue column shows claims that need review, with search and status/risk filters.
- The main workspace shows selected claim details, policy/coverage context, documents, timeline, and audit.
- A right intelligence rail shows AI triage, document intelligence, RAG assistant, and human review action.

The design should feel like a work tool: restrained, information-dense, clear status color, predictable navigation, and no oversized hero section.

## Layout

Desktop:

```text
Top bar
Queue column | Claim workspace | Intelligence rail
```

Mobile/tablet:

```text
Top bar
Queue selector
Tabs: Overview | Documents | Timeline | Intelligence | Audit
```

The implementation can use responsive CSS grid and a tab-like navigation on smaller screens without adding Vue Router in Phase 9.

## Visual Design

Use a calm enterprise palette:

- neutral background
- white and near-white panels
- blue for primary action/information
- amber for warnings
- red for high-risk signals
- green for covered/complete/low-risk signals

Avoid a one-note palette, decorative blobs, landing-page hero treatment, and card-within-card structures. Panels should be clear but restrained, with compact headings and stable dimensions for queue rows, score blocks, buttons, and tabs.

Use icon buttons where useful. If adding an icon dependency is practical, use `lucide-vue-next`; otherwise use text labels and simple CSS indicators for Phase 9.

## Data Model

The frontend will define typed demo data:

- `ClaimQueueItem`
- `ClaimDetail`
- `PolicySnapshot`
- `CustomerSnapshot`
- `TriageSnapshot`
- `DocumentIntelligenceSnapshot`
- `RagAnswer`
- `TimelineEvent`
- `AuditEvent`

The data mirrors the current backend and AI service contracts, but it is stored locally in Phase 9.

## Component Boundaries

Recommended components:

- `App.vue`: shell, selected claim state, modal state.
- `ClaimQueue.vue`: search/filter queue and emit selected claim.
- `ClaimOverview.vue`: claim facts, customer, policy, and coverage.
- `TriagePanel.vue`: AI risk scores and reason codes.
- `DocumentPanel.vue`: received/missing docs, extraction highlights, summary sections.
- `RagAssistant.vue`: sample question selector, grounded answer, source list.
- `TimelinePanel.vue`: chronological claim events.
- `AuditPanel.vue`: AI/RAG/human events.
- `HumanReviewModal.vue`: override action, reason text, decision-support warning.
- `demoData.ts`: local typed demo claims.
- `types.ts`: frontend domain types.

## Testing Strategy

Tests will cover:

- queue search/filter behavior;
- selecting a claim updates the detail workspace;
- triage panel renders risk labels, reason codes, and human-review indicator;
- RAG assistant renders sources for grounded answers and missing-evidence text when selected;
- human review modal captures selected action and reason text;
- production build succeeds.

Because Phase 9 is a frontend scaffold, the primary verification commands are:

```bash
cd frontend
npm test -- --run
npm run build
```

The root `scripts/run-tests.sh` will also include the frontend tests/build if `frontend/package.json` exists.

## Dependency And Setup Notes

The current repo only has a frontend placeholder. Phase 9 will add a standard `package.json` with Vue, Vite, TypeScript, Vitest, Vue Test Utils, jsdom, and optionally `lucide-vue-next`. Installing dependencies may require network access once in the local workspace.

No dependency lockfile should be hand-authored. It should be generated by the package manager during install.

## Documentation Updates

Phase 9 will add:

- `frontend/README.md` update with setup, scripts, and demo story.
- `docs/frontend/adjuster-workbench.md`.
- README and docs index links.
- Project memory entries for start, implementation, verification, and PR.

## Done Criteria

Phase 9 is done when:

- Design and implementation plan are committed.
- Vue workbench opens directly to the claim queue/workspace.
- Demo claim story shows policy context, claim timeline, AI triage, document intelligence, RAG answer, and human review.
- Component tests pass.
- Production build passes.
- Root verification includes frontend checks.
- Project memory is updated.
- A pull request is opened from `adjuster-workbench-frontend` into `main`.
