# Dynamic Claims Application Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Document the next InsureFlow AI productization roadmap from the single-page demo workbench to a live multi-page claims application.

**Architecture:** Keep this as planning/documentation work only. The roadmap defines Phases 15-20 and avoids frontend implementation until a phase-specific plan is approved.

**Tech Stack:** Markdown documentation, existing docs index, existing project memory.

---

## Task 1: Add Product Roadmap Document

**Files:**
- Create: `docs/product/dynamic-claims-application-roadmap.md`

- [x] **Step 1: Create the roadmap**

Document the current state, missing product capabilities, six new phases, target page map, data flow, demo mode strategy, testing strategy, documentation strategy, and recommended execution order.

- [x] **Step 2: Verify the roadmap has no placeholders**

Search for placeholder markers and vague future-only language. The roadmap should name concrete phases, branch names, pages, data sources, and success criteria.

## Task 2: Add Design Spec

**Files:**
- Create: `docs/superpowers/specs/2026-06-30-dynamic-claims-application-design.md`

- [x] **Step 1: Create the design spec**

Summarize the product boundary, page model, architecture direction, data strategy, error handling, testing strategy, and recommended first phase.

- [x] **Step 2: Keep the design implementation-free**

The spec should not add Vue Router code, API clients, or backend changes. It should prepare the next phase rather than implement it.

## Task 3: Link Documentation

**Files:**
- Modify: `docs/README.md`

- [x] **Step 1: Add product roadmap link**

Add `docs/product/dynamic-claims-application-roadmap.md` to the documentation index under a new or existing section that clearly separates future productization from completed implementation history.

## Task 4: Update Project Memory

**Files:**
- Modify: `PROJECT_MEMORY.md`

- [x] **Step 1: Add roadmap decision**

Record that the post-Phase-14 evolution will use Phases 15-20, beginning with frontend routing and app shell before live backend integration.

- [x] **Step 2: Add near-term next step**

Update the near-term next steps to include reviewing the dynamic claims application roadmap and then starting Phase 15 on `frontend-routing-shell`.

## Task 5: Verify Documentation

**Files:**
- Read: `docs/product/dynamic-claims-application-roadmap.md`
- Read: `docs/superpowers/specs/2026-06-30-dynamic-claims-application-design.md`
- Read: `docs/README.md`
- Read: `PROJECT_MEMORY.md`

- [x] **Step 1: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

- [x] **Step 2: Confirm roadmap files are tracked as changes**

Run:

```bash
git status --short
```

Expected: the roadmap, design spec, docs index, project memory, and this plan appear as modified or added files.
