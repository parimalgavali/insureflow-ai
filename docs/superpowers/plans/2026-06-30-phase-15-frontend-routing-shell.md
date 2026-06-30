# Phase 15 Frontend App Shell And Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the demo-data-first adjuster workbench into a routed multi-page Vue application shell while preserving the existing portfolio demo behavior.

**Architecture:** Add Vue Router and split the current single `App.vue` composition into a persistent shell plus route pages. Keep demo data as the source for Phase 15 so live API integration can happen cleanly in Phase 16.

**Tech Stack:** Vue 3, Vite, TypeScript, Vue Router 4, Vitest, Vue Test Utils.

---

## Task 1: Add Phase 15 Router Tests

**Files:**
- Modify: `frontend/src/test/App.spec.ts`
- Modify: `frontend/src/test/components.spec.ts`

- [x] **Step 1: Write route behavior tests**

Add tests for:

- `/` redirects to `/claims`.
- `/claims` renders the claim queue page.
- Selecting a queue claim navigates to `/claims/:claimNumber`.
- `/claims/:claimNumber` renders claim detail widgets.
- `/claims/:claimNumber/review` renders a route-backed human review page.
- Supporting navigation links exist for documents, governance, integrations, and settings.

- [x] **Step 2: Run tests and verify failure**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: tests fail because Vue Router, route pages, and router setup do not exist yet.

## Task 2: Add Router Dependency And Router Module

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Create: `frontend/src/router.ts`

- [x] **Step 1: Install Vue Router**

Run:

```bash
cd frontend
npm install vue-router@^4.5.1
```

- [x] **Step 2: Create router module**

Create a router with routes:

- `/` redirects to `/claims`
- `/claims`
- `/claims/:claimNumber`
- `/claims/:claimNumber/review`
- `/documents`
- `/governance`
- `/integrations`
- `/settings`

## Task 3: Create Routed App Shell And Pages

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/main.ts`
- Create: `frontend/src/pages/ClaimsPage.vue`
- Create: `frontend/src/pages/ClaimDetailPage.vue`
- Create: `frontend/src/pages/HumanReviewPage.vue`
- Create: `frontend/src/pages/DocumentsPage.vue`
- Create: `frontend/src/pages/GovernancePage.vue`
- Create: `frontend/src/pages/IntegrationsPage.vue`
- Create: `frontend/src/pages/SettingsPage.vue`

- [x] **Step 1: Convert `App.vue` into persistent shell**

Keep topbar branding and add navigation links. Render current route content through `RouterView`.

- [x] **Step 2: Move claim queue behavior into `ClaimsPage.vue`**

Use `ClaimQueue.vue` with demo claims. On selection, route to `/claims/:claimNumber`.

- [x] **Step 3: Move claim detail workbench into `ClaimDetailPage.vue`**

Use existing detail widgets and selected claim route param. Include a route link to the human review page.

- [x] **Step 4: Add route-backed human review page**

Use existing `HumanReviewModal.vue` behavior to capture review action and reason, then show the submitted action on the page.

- [x] **Step 5: Add supporting pages**

Add lightweight operational pages for documents, governance, integrations, and settings.

## Task 4: Update Styles And Documentation

**Files:**
- Modify: `frontend/src/styles.css`
- Modify: `docs/frontend/adjuster-workbench.md`
- Modify: `PROJECT_MEMORY.md`

- [x] **Step 1: Add shell/page styles**

Add navigation, page header, and placeholder page styles without breaking the existing workbench grid.

- [x] **Step 2: Update frontend docs**

Explain that Phase 15 adds routing and page boundaries while keeping demo data.

- [x] **Step 3: Update project memory**

Record Phase 15 start, branch name, and implementation scope.

## Task 5: Verify Phase 15

**Files:**
- Read: frontend source and docs changed in this phase.

- [x] **Step 1: Run frontend tests**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: all frontend tests pass.

- [x] **Step 2: Run frontend build**

Run:

```bash
cd frontend
npm run build
```

Expected: TypeScript check and Vite production build pass.

- [x] **Step 3: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.
