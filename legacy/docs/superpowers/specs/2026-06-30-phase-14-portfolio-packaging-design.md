# Phase 14 Portfolio Packaging Design

## Purpose

Phase 14 turns InsureFlow AI from a feature-complete engineering project into a recruiter-ready portfolio package. The goal is to make the project understandable in five minutes, credible in a technical interview, and easy to run or inspect from a fresh clone.

The package must keep the project boundary clear: InsureFlow AI is Guidewire-inspired, synthetic-data-based, and not an official Guidewire implementation, connector, certification, or product.

## Scope

Phase 14 will add:

- A polished root README structure that leads with problem, solution, architecture, demo path, and proof points.
- A documentation index that separates evaluator-facing docs from build-history docs.
- Demo documentation under `docs/demo/`:
  - five-minute demo script;
  - recruiter walkthrough;
  - interview talking points;
  - screenshot capture checklist.
- Portfolio documentation under `docs/portfolio/`:
  - resume bullets;
  - project narrative;
  - LinkedIn/GitHub summary.
- Architecture and workflow diagrams embedded as Mermaid so they render on GitHub without external assets.
- A final responsible AI statement that ties together rules, ML, document intelligence, RAG, human review, audit, and synthetic-data limitations.
- Project memory updates for Phase 14 start and implementation.

Phase 14 will not require recording an actual video, deploying a public cloud endpoint, adding new runtime services, or changing business logic.

## Primary Audience

The documentation should serve three reader modes:

1. Recruiter or hiring manager: can understand the project value, tech stack, and candidate signal quickly.
2. Technical interviewer: can drill into architecture, testing, observability, AI boundaries, and trade-offs.
3. Future maintainer or agent: can find docs, run verification, and continue the project without re-reading every phase plan.

## Documentation Architecture

The root README becomes the project front door. It should answer:

- What problem does this simulate?
- What does the system do?
- What makes it Guidewire-relevant without claiming affiliation?
- How is the system architected?
- How can someone run the demo?
- Where are detailed docs?
- What are the responsible AI boundaries?

`docs/README.md` becomes the documentation map. It should group links by use case:

- evaluator quick path;
- architecture and domain;
- APIs and services;
- AI/ML and responsible AI;
- deployment, quality, and observability;
- implementation history.

`docs/demo/` becomes the live demo package. It should describe a single coherent scenario: a policyholder reports an auto collision, the system validates policy/coverage, creates a claim, runs AI triage, enriches with document intelligence, uses RAG for adjuster assistance, records audit/governance signals, and exposes integration APIs.

`docs/portfolio/` becomes the career packaging layer. It should translate the project into resume bullets, a short project narrative, and concise public profile copy without exaggerating production readiness.

## Demo Story

The default demo narrative:

1. Introduce InsureFlow AI as a synthetic P&C claims intelligence platform.
2. Show the Vue adjuster workbench for claim queue and claim detail context.
3. Explain backend workflow: policy, coverage, FNOL, lifecycle, notes, documents, timeline.
4. Show AI triage: rule baseline, ML artifacts, severity/fraud/litigation signals, human review.
5. Show document intelligence and RAG assistant as decision-support tools.
6. Show governance: audit trail, correlation IDs, model/prompt registry, human override.
7. Show deployment and quality: Docker Compose app profile, cloud templates, CI, coverage, Trivy, Prometheus/Grafana.
8. Close with responsible AI boundaries and what this proves technically.

The script should be runnable even if a reviewer only reads it. Commands should favor local, reproducible paths already in the repo.

## Diagrams

Use Mermaid in Markdown for portability:

- System architecture diagram in README.
- Claim intelligence workflow in demo docs.
- AI decision-support flow in responsible AI docs.
- Evaluator navigation map in docs index if useful.

No generated image files are required in this phase.

## Verification

Phase 14 verification should prove docs and package quality:

- `git diff --check`
- Markdown link/path sanity for new local docs.
- Existing quality command if practical: `./scripts/run-quality-gates.sh`
- README command blocks should reference existing scripts or directories.

Because Phase 14 is documentation-heavy, successful verification is based on link integrity, coherent docs, and no accidental generated artifacts.

## Risks And Mitigations

- Risk: over-claiming Guidewire affiliation.
  Mitigation: repeat the Guidewire-inspired boundary in README, demo, portfolio narrative, and responsible AI docs.

- Risk: docs become too long for recruiters.
  Mitigation: README should provide quick summaries and link to details rather than duplicating every phase.

- Risk: demo script depends on an unavailable cloud deployment.
  Mitigation: keep the primary path local Docker Compose and document cloud deployment as readiness, not a required live demo.

- Risk: screenshot/video production slows completion.
  Mitigation: include a screenshot checklist and capture slots, but do not require media files for Phase 14 completion.

## Acceptance Criteria

- Root README reads as a polished portfolio front page.
- `docs/README.md` points evaluators to the fastest useful path.
- `docs/demo/demo-script.md` provides a five-minute demo path.
- `docs/demo/recruiter-walkthrough.md` explains the project in non-jargony terms.
- `docs/demo/interview-talking-points.md` prepares deeper technical discussion.
- `docs/demo/screenshot-checklist.md` identifies the screenshots to capture later.
- `docs/portfolio/resume-bullets.md` contains honest, role-aligned resume bullets.
- `docs/portfolio/project-narrative.md` contains a concise story suitable for GitHub/LinkedIn.
- `docs/ai/responsible-ai-statement.md` or equivalent central doc clearly defines AI limitations and governance controls.
- `PROJECT_MEMORY.md` records Phase 14 progress.
