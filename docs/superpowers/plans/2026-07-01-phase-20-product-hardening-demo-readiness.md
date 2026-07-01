# Phase 20 Product Hardening And Demo Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the dynamic InsureFlow AI application easier to run, verify, and present as a finished portfolio demo.

**Architecture:** Add a small frontend demo-readiness model and surface it on the settings page so the app itself explains demo health and run modes. Add a repository-level readiness script that validates key docs and runs frontend smoke checks. Update demo, frontend, roadmap, README, docs index, and project memory so the completed Phase 15-20 dynamic app is accurately described.

**Tech Stack:** Bash, Vue 3, TypeScript, Vitest, Vue Test Utils, Markdown.

---

## Task 1: Add Frontend Demo Readiness Checklist

**Files:**
- Modify: `frontend/src/test/App.spec.ts`
- Create: `frontend/src/services/demoReadiness.ts`
- Modify: `frontend/src/pages/SettingsPage.vue`
- Modify: `frontend/src/styles.css`

- [x] **Step 1: Write failing settings route test**

Add a test that opens `/settings` and expects:

```ts
expect(wrapper.text()).toContain("Demo Readiness");
expect(wrapper.text()).toContain("Frontend smoke");
expect(wrapper.text()).toContain("Docker app profile");
expect(wrapper.text()).toContain("VITE_DATA_MODE");
```

- [x] **Step 2: Run frontend tests and verify failure**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: fail because the settings page still shows a small placeholder.

- [x] **Step 3: Implement demo-readiness data and settings UI**

Create `frontend/src/services/demoReadiness.ts` with:

```ts
export const demoReadinessChecks = [
  {
    label: "Frontend smoke",
    detail: "Queue, claim detail, review, documents, governance, integrations, and settings routes are covered by Vitest.",
  },
  {
    label: "Docker app profile",
    detail: "Run docker compose --profile app up --build and scripts/smoke-test-containers.sh for container demo validation.",
  },
  {
    label: "Live backend mode",
    detail: "Set VITE_DATA_MODE=live to call the Spring Boot API through the Vite or nginx /api proxy.",
  },
];
```

Render these checks on `SettingsPage.vue` with compact cards and keep the data-mode/API connection context visible.

- [x] **Step 4: Run frontend tests and verify pass**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: pass.

## Task 2: Add Demo Readiness Script

**Files:**
- Create: `scripts/demo-readiness-check.sh`

- [x] **Step 1: Add script**

Create a script that checks required demo docs exist, runs frontend tests and build, and prints the app-profile smoke command to run after containers start.

- [x] **Step 2: Validate script syntax**

Run:

```bash
bash -n scripts/demo-readiness-check.sh
```

Expected: no output and exit code 0.

## Task 3: Update Demo And Product Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/demo/demo-script.md`
- Modify: `docs/frontend/adjuster-workbench.md`
- Modify: `docs/product/dynamic-claims-application-roadmap.md`
- Modify: `PROJECT_MEMORY.md`

- [x] **Step 1: Update docs for completed dynamic app**

Document:

- Phase 20 settings readiness panel
- `scripts/demo-readiness-check.sh`
- completed Phases 15-20
- remaining honest limitations: file upload, production auth UI, full audit pagination/date filters

- [x] **Step 2: Update project memory**

Record the Phase 20 branch, scope, verification, and next recommendation.

## Task 4: Final Verification

- [x] **Step 1: Run frontend tests**

```bash
cd frontend
npm test -- --run
```

- [x] **Step 2: Run frontend build**

```bash
cd frontend
npm run build
```

- [x] **Step 3: Run demo readiness script syntax check**

```bash
bash -n scripts/demo-readiness-check.sh
```

- [x] **Step 4: Run whitespace check**

```bash
git diff --check
```

Expected: all commands pass.
