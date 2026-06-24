# InsureFlow AI Project Memory

This file is the living memory for the InsureFlow AI project. Update it after important decisions, completed phases, repository changes, architecture choices, blockers, and handoffs.

Future Codex sessions should read this file before planning or implementing work.

## Current Project State

- **Project name:** InsureFlow AI
- **GitHub repository:** https://github.com/parimalgavali/insureflow-ai
- **Visibility:** Public
- **Local workspace:** `/Users/parimal_gavali/Documents/Guidewire`
- **Primary blueprint source:** `/Users/parimal_gavali/Developer/Guidewire/InsureFlow_AI_Complete_Project_Blueprint.md`
- **Current branch:** `codex/project-memory-and-phase-plans`
- **First committed artifact:** `docs/superpowers/plans/2026-06-24-insureflow-ai-master-build-plan.md`

## Project Purpose

InsureFlow AI is a Guidewire-inspired, cloud-native claims and policy intelligence portfolio project. It is designed to demonstrate insurance domain understanding, Java/Spring Boot backend engineering, AI/ML model serving, LLM/RAG document intelligence, auditability, and human-in-the-loop responsible AI.

The career positioning is:

> I may not yet have professional Guidewire implementation experience, but I understand insurance workflows around policy and claims, I can build enterprise-grade Java integrations, and I can responsibly integrate AI/ML/LLM intelligence into insurance operations.

## Execution Strategy

Use a phase-based agent approach first, then evolve into a three-agent split once foundations and contracts exist.

Recommended sequence:

1. Build Phase 0 and Phase 1 with a foundation-focused worker.
2. After backend/domain/API contracts exist, parallelize:
   - Backend agent for policy, claims, audit, security, integration APIs.
   - AI/middleware agent for synthetic data, triage, ML, LLM, RAG.
   - Frontend agent for Vue adjuster workbench.
3. The main Codex session acts as orchestrator: contracts, review, integration, tests, and GitHub coordination.

## Key Decisions

| Date | Decision | Reason |
| --- | --- | --- |
| 2026-06-24 | Use `InsureFlow AI` as the project name. | Matches the blueprint and clearly communicates insurance workflow intelligence. |
| 2026-06-24 | Start with phase-based agents before splitting into permanent frontend/backend/AI agents. | The repo starts empty, so foundation and contracts must come before parallel feature work. |
| 2026-06-24 | Keep the GitHub repository public. | This is a professional portfolio project intended for recruiters and hiring managers. |
| 2026-06-24 | Use the master build plan as the roadmap and create detailed phase plans as work begins. | Prevents the large blueprint from becoming an unmanageable single implementation pass. |
| 2026-06-24 | Keep feature work off `main`; use `codex/` feature branches. | Keeps the public portfolio branch stable while implementation work is reviewed. |

## Completed Work

| Date | Work | Evidence |
| --- | --- | --- |
| 2026-06-24 | Read and summarized the full project blueprint. | Blueprint reviewed from `/Users/parimal_gavali/Developer/Guidewire/InsureFlow_AI_Complete_Project_Blueprint.md`. |
| 2026-06-24 | Created the master build plan. | `docs/superpowers/plans/2026-06-24-insureflow-ai-master-build-plan.md` |
| 2026-06-24 | Connected the project to GitHub. | `https://github.com/parimalgavali/insureflow-ai` |
| 2026-06-24 | Confirmed master build plan exists on GitHub. | `main` contains commit `f68ed27`. |
| 2026-06-24 | Created feature branch for memory and Phase 0/1 planning. | Branch `codex/project-memory-and-phase-plans`. |
| 2026-06-24 | Created detailed Phase 0/1 implementation plan. | `docs/superpowers/plans/2026-06-24-phase-0-1-repository-and-domain-foundation.md` |

## Known Issues And Caveats

- `gh auth status` previously reported an invalid token even though the first project commit reached GitHub. Recheck GitHub CLI auth before future push/PR workflows.
- The local workspace currently contains planning/memory artifacts, not the full project scaffold yet.
- The blueprint file lives outside the repo. It should be copied into the repo as `PROJECT_BLUEPRINT.md` during Phase 0 if licensing/privacy is acceptable.

## Near-Term Next Steps

1. Commit the memory and Phase 0/1 planning updates on `codex/project-memory-and-phase-plans`.
2. Execute the detailed Phase 0/1 implementation plan.
3. Implement repository structure, README, `.gitignore`, `.env.example`, Docker Compose, CI skeleton, and docs starter files.
4. Add backend Spring Boot skeleton and database/Flyway foundation.
5. Verify local infrastructure and schema tests.
6. Commit, push, and open a PR back to `main`.

## Memory Update Rules

Update this file whenever:

- A phase starts or finishes.
- A major architecture or technology decision is made.
- A GitHub branch, PR, commit, or release is created.
- A blocker appears or is resolved.
- Agent ownership changes.
- A contract between backend, AI, and frontend changes.
- A deployment, demo, or portfolio artifact is published.

Keep entries concise and dated. Prefer links to documents, commits, PRs, and local files instead of long explanations.
