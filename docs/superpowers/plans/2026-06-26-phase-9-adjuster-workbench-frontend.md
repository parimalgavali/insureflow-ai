# Phase 9 Adjuster Workbench Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a recruiter-friendly Vue adjuster workbench that shows the full InsureFlow AI claim intelligence story from queue to claim detail, AI triage, document intelligence, RAG assistance, timeline, audit, and human review.

**Architecture:** Add a Vue 3/Vite/TypeScript app under `frontend` using local typed demo data and component-level state. Keep backend integration behind a future adapter boundary; Phase 9 focuses on a polished, offline, testable workbench that demonstrates the domain and AI workflows immediately.

**Tech Stack:** Vue 3, Vite, TypeScript, Vitest, Vue Test Utils, jsdom, CSS grid/flexbox.

---

## File Structure

- Create/modify `frontend/package.json`
- Create `frontend/index.html`
- Create `frontend/tsconfig.json`
- Create `frontend/tsconfig.node.json`
- Create `frontend/vite.config.ts`
- Create `frontend/src/main.ts`
- Create `frontend/src/App.vue`
- Create `frontend/src/styles.css`
- Create `frontend/src/types.ts`
- Create `frontend/src/demoData.ts`
- Create `frontend/src/components/ClaimQueue.vue`
- Create `frontend/src/components/ClaimOverview.vue`
- Create `frontend/src/components/TriagePanel.vue`
- Create `frontend/src/components/DocumentPanel.vue`
- Create `frontend/src/components/RagAssistant.vue`
- Create `frontend/src/components/TimelinePanel.vue`
- Create `frontend/src/components/AuditPanel.vue`
- Create `frontend/src/components/HumanReviewModal.vue`
- Create `frontend/src/test/App.spec.ts`
- Create `frontend/src/test/components.spec.ts`
- Create `docs/frontend/adjuster-workbench.md`
- Modify `frontend/README.md`
- Modify `README.md`
- Modify `docs/README.md`
- Modify `scripts/run-tests.sh`
- Modify `PROJECT_MEMORY.md`

## Task 1: Documentation Foundation

**Files:**
- Create: `docs/superpowers/specs/2026-06-26-phase-9-adjuster-workbench-frontend-design.md`
- Create: `docs/superpowers/plans/2026-06-26-phase-9-adjuster-workbench-frontend.md`
- Modify: `PROJECT_MEMORY.md`

- [ ] **Step 1: Confirm branch**

Run: `git status --short --branch`

Expected: branch is `adjuster-workbench-frontend`.

- [ ] **Step 2: Write design and plan docs**

Document scope, UI layout, data model, component boundaries, test strategy, setup, and done criteria.

- [ ] **Step 3: Update project memory**

Add:

```markdown
| 2026-06-26 | Started Phase 9 adjuster workbench frontend. | Branch `adjuster-workbench-frontend`; design and implementation plan created for the Vue workbench. |
```

- [ ] **Step 4: Commit documentation**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-phase-9-adjuster-workbench-frontend-design.md docs/superpowers/plans/2026-06-26-phase-9-adjuster-workbench-frontend.md PROJECT_MEMORY.md
git commit -m "docs: design phase 9 adjuster workbench"
```

## Task 2: Frontend Scaffold And First Failing Tests

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/test/App.spec.ts`

- [ ] **Step 1: Write failing app smoke test**

Create an app test that mounts `App.vue` and expects:

- `Claim Queue` heading;
- selected claim number;
- `AI Triage`;
- `RAG Assistant`;
- `Human Review`.

Run:

```bash
cd frontend
npm test -- --run src/test/App.spec.ts
```

Expected: fails because the Vue app does not exist yet.

- [ ] **Step 2: Add package and Vite scaffold**

Add Vue/Vite/TypeScript/Vitest configuration and a minimal `App.vue`.

- [ ] **Step 3: Install dependencies**

Run:

```bash
cd frontend
npm install
```

Expected: `node_modules` and `package-lock.json` are generated.

- [ ] **Step 4: Run app smoke test**

Run:

```bash
cd frontend
npm test -- --run src/test/App.spec.ts
```

Expected: test passes after minimal app scaffold.

- [ ] **Step 5: Commit scaffold**

Run:

```bash
git add frontend
git commit -m "feat: scaffold adjuster workbench"
```

## Task 3: Demo Data And Workbench Components

**Files:**
- Create: `frontend/src/types.ts`
- Create: `frontend/src/demoData.ts`
- Create: `frontend/src/components/ClaimQueue.vue`
- Create: `frontend/src/components/ClaimOverview.vue`
- Create: `frontend/src/components/TriagePanel.vue`
- Create: `frontend/src/components/DocumentPanel.vue`
- Create: `frontend/src/components/RagAssistant.vue`
- Create: `frontend/src/components/TimelinePanel.vue`
- Create: `frontend/src/components/AuditPanel.vue`
- Create: `frontend/src/components/HumanReviewModal.vue`
- Modify: `frontend/src/App.vue`
- Test: `frontend/src/test/components.spec.ts`

- [ ] **Step 1: Write failing component tests**

Create tests that prove:

- queue search filters claims by number/customer;
- selecting a queue claim updates the displayed claim detail;
- triage panel displays severity/fraud/litigation labels and reason codes;
- RAG assistant displays answer sources;
- human review modal captures action and reason.

Run:

```bash
cd frontend
npm test -- --run src/test/components.spec.ts
```

Expected: fails because components and demo data do not exist yet.

- [ ] **Step 2: Add typed demo data**

Create two or three realistic claims, including:

- one high-severity motor collision with missing police report;
- one medium property claim;
- one low-risk claim.

- [ ] **Step 3: Implement components**

Use compact, domain-specific components. Keep `App.vue` as the composition shell and selected-claim state owner.

- [ ] **Step 4: Run component tests**

Run:

```bash
cd frontend
npm test -- --run src/test/components.spec.ts
```

Expected: tests pass.

- [ ] **Step 5: Commit components**

Run:

```bash
git add frontend/src
git commit -m "feat: build adjuster workbench components"
```

## Task 4: Responsive Styling And Documentation

**Files:**
- Create: `frontend/src/styles.css`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/README.md`
- Create: `docs/frontend/adjuster-workbench.md`
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `scripts/run-tests.sh`
- Modify: `PROJECT_MEMORY.md`

- [ ] **Step 1: Add responsive operational styling**

Use CSS grid/flexbox, compact panels, stable button/control sizes, and mobile-friendly stacking. Avoid landing-page hero treatment.

- [ ] **Step 2: Document local frontend workflow**

Document:

- install command;
- test command;
- build command;
- dev server command;
- demo story;
- offline demo-data-first boundary.

- [ ] **Step 3: Update root test script**

Add frontend test/build block when `frontend/package.json` exists:

```bash
if [ -f "$ROOT_DIR/frontend/package.json" ]; then
  (cd "$ROOT_DIR/frontend" && npm test -- --run && npm run build)
fi
```

- [ ] **Step 4: Update project memory**

Record Phase 9 implementation progress.

- [ ] **Step 5: Run focused frontend checks**

Run:

```bash
cd frontend
npm test -- --run
npm run build
```

Expected: tests and build pass.

- [ ] **Step 6: Commit docs and styling**

Run:

```bash
git add frontend README.md docs/README.md docs/frontend/adjuster-workbench.md scripts/run-tests.sh PROJECT_MEMORY.md
git commit -m "docs: document phase 9 adjuster workbench"
```

## Task 5: Full Verification And Pull Request

**Files:**
- No source edits expected unless verification finds an issue.

- [ ] **Step 1: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 2: Run full repository tests**

Run:

```bash
./scripts/run-tests.sh
```

Expected: backend, synthetic generator, triage service, document intelligence service, RAG service, ML package, and frontend checks pass.

- [ ] **Step 3: Record verification and open PR**

Update `PROJECT_MEMORY.md`, commit, push `adjuster-workbench-frontend`, and open a PR into `main`.

## Self-Review Checklist

- First screen is the usable workbench, not a landing page.
- The UI shows claim queue, claim detail, policy, timeline, documents, triage, RAG, audit, and human review.
- AI outputs are framed as decision support.
- The app can run offline with local demo data.
- Tests and production build are part of verification.
