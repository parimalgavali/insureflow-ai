# Phase 14 Portfolio Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package InsureFlow AI as a polished recruiter-facing and interviewer-ready portfolio project.

**Architecture:** Keep runtime code unchanged and add a documentation layer that acts as the public front door. The root README becomes the short evaluator path, `docs/demo/` becomes the demo package, `docs/portfolio/` becomes the career narrative package, and `docs/ai/` centralizes responsible AI framing.

**Tech Stack:** Markdown, Mermaid diagrams, existing Docker Compose scripts, existing CI/quality scripts.

---

## File Structure

- Modify `README.md`: rewrite as a polished portfolio front page with problem, solution, architecture, proof points, local demo, docs map, and responsible AI boundary.
- Modify `docs/README.md`: reorganize links by evaluator use case and add Phase 14 deliverables.
- Create `docs/demo/demo-script.md`: five-minute local demo script.
- Create `docs/demo/recruiter-walkthrough.md`: non-jargony walkthrough for recruiters and hiring managers.
- Create `docs/demo/interview-talking-points.md`: deeper technical discussion prompts and answers.
- Create `docs/demo/screenshot-checklist.md`: screenshot capture checklist and recommended filenames.
- Create `docs/portfolio/resume-bullets.md`: honest resume bullets grouped by role angle.
- Create `docs/portfolio/project-narrative.md`: concise GitHub/LinkedIn/project story.
- Create `docs/ai/responsible-ai-statement.md`: central responsible AI statement for rules, ML, LLM, RAG, governance, and synthetic data.
- Modify `PROJECT_MEMORY.md`: record Phase 14 design, implementation, and verification.

## Task 1: Portfolio README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the current README with a recruiter-ready structure**

Use this section order:

```markdown
# InsureFlow AI

## What This Is
## Why It Matters
## What It Demonstrates
## Architecture
## Five-Minute Demo
## System Capabilities
## Tech Stack
## Local Run Commands
## Documentation Map
## Responsible AI And Project Boundary
```

- [ ] **Step 2: Add Mermaid architecture diagram**

Include one GitHub-renderable Mermaid diagram showing frontend, backend, data, AI services, integrations, cloud templates, quality, and observability.

- [ ] **Step 3: Verify README command paths**

Run:

```bash
test -f scripts/run-tests.sh
test -f scripts/run-quality-gates.sh
test -f scripts/smoke-test-containers.sh
test -d frontend
test -d backend
test -d ai-services
```

Expected: all commands exit `0`.

## Task 2: Demo Package

**Files:**
- Create: `docs/demo/demo-script.md`
- Create: `docs/demo/recruiter-walkthrough.md`
- Create: `docs/demo/interview-talking-points.md`
- Create: `docs/demo/screenshot-checklist.md`

- [ ] **Step 1: Create the five-minute demo script**

The script must walk through local startup, frontend workbench, policy/FNOL, AI triage, document intelligence, RAG, governance, quality, and closing pitch.

- [ ] **Step 2: Create recruiter walkthrough**

Use plain language and explain why the project matters for insurance technology, Guidewire-adjacent roles, Java/cloud engineering, and AI governance.

- [ ] **Step 3: Create interview talking points**

Include concise answers for architecture, domain model, AI design, ML limitations, RAG grounding, governance, CI/security, deployment, and trade-offs.

- [ ] **Step 4: Create screenshot checklist**

List expected screenshot names and what each screenshot should show. Do not require binary image files in this phase.

## Task 3: Portfolio Narrative Package

**Files:**
- Create: `docs/portfolio/resume-bullets.md`
- Create: `docs/portfolio/project-narrative.md`

- [ ] **Step 1: Create role-aligned resume bullets**

Group bullets for:

- Java backend / insurance platform engineer;
- AI/ML application engineer;
- cloud/platform engineer;
- full-stack engineer;
- concise master version.

- [ ] **Step 2: Create public project narrative**

Include short, medium, and long versions suitable for GitHub, LinkedIn, and interview introductions.

## Task 4: Responsible AI Statement

**Files:**
- Create: `docs/ai/responsible-ai-statement.md`

- [ ] **Step 1: Document AI boundaries**

Cover:

- decision-support only;
- synthetic data;
- rule-based triage;
- ML model cards;
- document intelligence;
- RAG grounding;
- human review;
- audit and governance;
- prohibited uses.

- [ ] **Step 2: Link existing governance docs**

Reference:

- `docs/api/security-audit-governance.md`
- `docs/ml/severity-model-card.md`
- `docs/ml/fraud-risk-model-card.md`
- `docs/api/ai-triage.md`
- `docs/api/document-intelligence.md`
- `docs/api/rag-assistant.md`

## Task 5: Documentation Index And Memory

**Files:**
- Modify: `docs/README.md`
- Modify: `PROJECT_MEMORY.md`

- [ ] **Step 1: Update docs index**

Add the evaluator quick path and links to all Phase 14 deliverables.

- [ ] **Step 2: Update project memory**

Add entries for:

- Phase 14 design started;
- Phase 14 portfolio package implemented;
- Phase 14 verification.

## Task 6: Verification And Pull Request

**Files:**
- Review all modified and created files.

- [ ] **Step 1: Run whitespace verification**

Run:

```bash
git diff --check
```

Expected: no output and exit `0`.

- [ ] **Step 2: Run local doc path sanity checks**

Run:

```bash
test -f docs/demo/demo-script.md
test -f docs/demo/recruiter-walkthrough.md
test -f docs/demo/interview-talking-points.md
test -f docs/demo/screenshot-checklist.md
test -f docs/portfolio/resume-bullets.md
test -f docs/portfolio/project-narrative.md
test -f docs/ai/responsible-ai-statement.md
```

Expected: all commands exit `0`.

- [ ] **Step 3: Run quality gates if local dependencies are available**

Run:

```bash
./scripts/run-quality-gates.sh
```

Expected: all configured quality gates pass. If it fails due local tooling or environment, capture the reason.

- [ ] **Step 4: Commit Phase 14 implementation**

Run:

```bash
git add README.md docs/README.md docs/demo docs/portfolio docs/ai PROJECT_MEMORY.md docs/superpowers/plans/2026-06-30-phase-14-portfolio-packaging.md
git commit -m "docs: package insureflow ai portfolio demo"
```

- [ ] **Step 5: Push and open PR**

Run:

```bash
git push -u origin portfolio-packaging
gh pr create --base main --head portfolio-packaging --title "Phase 14: Portfolio packaging" --body "<summary and verification>"
```

## Self-Review

- Spec coverage: The plan covers README polish, demo package, recruiter walkthrough, interview talking points, screenshot checklist, portfolio narrative, resume bullets, responsible AI statement, docs index, memory update, and verification.
- Placeholder scan: No task depends on TBD content or unspecified files.
- Type consistency: File paths match the Phase 14 design and repository conventions.
