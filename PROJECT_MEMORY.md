# InsureFlow AI Project Memory

This file is the living memory for the InsureFlow AI project. Update it after important decisions, completed phases, repository changes, architecture choices, blockers, and handoffs.

Future Codex sessions should read this file before planning or implementing work.

## Current Project State

- **Project name:** InsureFlow AI
- **GitHub repository:** https://github.com/parimalgavali/insureflow-ai
- **Visibility:** Public
- **Local workspace:** `/Users/parimal_gavali/Documents/Guidewire`
- **Primary blueprint source:** `/Users/parimal_gavali/Developer/Guidewire/InsureFlow_AI_Complete_Project_Blueprint.md`
- **Current branch:** `codex/phase-2-synthetic-data-generator`
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
| 2026-06-24 | Pushed memory and Phase 0/1 planning branch to GitHub. | Remote branch `origin/codex/project-memory-and-phase-plans`. |
| 2026-06-24 | Started Phase 0/1 foundation branch. | Branch `codex/project-memory-and-phase-plans`. |
| 2026-06-24 | Completed Phase 0/1 repository and backend foundation. | Local infra, backend skeleton, Flyway schema, CI, and tests added on `codex/project-memory-and-phase-plans`. |
| 2026-06-24 | Verified Phase 0/1 foundation locally. | Docker Compose PostgreSQL/RabbitMQ healthy; `mvn test` and `./scripts/run-tests.sh` passed with 2 backend tests. |
| 2026-06-24 | Completed spec and quality review for Phase 0/1. | Spec compliant after push; quality review passed with no blocking issues. |
| 2026-06-24 | Started Phase 2 synthetic data generator branch. | Branch `codex/phase-2-synthetic-data-generator`, stacked on Phase 0/1 foundation until that PR merges. |
| 2026-06-24 | Completed Phase 2 synthetic data generator. | Generator creates relational CSVs, synthetic documents, labels, tests, and documentation. |
| 2026-06-24 | Verified Phase 2 locally. | Python generator tests passed; sample and default datasets generated successfully; backend tests still passed. |
| 2026-06-25 | Fixed Phase 2 review findings. | Added regression coverage so generated police/medical documents cannot contradict claim facts; updated root README Python commands. |
| 2026-06-25 | Re-verified Phase 2 after fixes. | `./scripts/run-tests.sh` passed: backend 2 tests and generator 10 tests. |
| 2026-06-25 | Pushed Phase 2 synthetic data generator branch to GitHub. | Remote branch `origin/codex/phase-2-synthetic-data-generator`. |

## Known Issues And Caveats

- `gh auth status` previously reported an invalid token even though the first project commit reached GitHub. Recheck GitHub CLI auth before future push/PR workflows.
- The local workspace now contains the Phase 0/1 project scaffold, backend Maven skeleton, and Flyway schema foundation.
- The blueprint file has been copied into the repo as `PROJECT_BLUEPRINT.md`; the original source remains `/Users/parimal_gavali/Developer/Guidewire/InsureFlow_AI_Complete_Project_Blueprint.md`.
- Maven was installed with Homebrew during Phase 0/1 verification and is now available as Maven 3.9.16.
- Docker Desktop was started during Phase 0/1 verification and local Compose/Testcontainers verification passed.
- Local Java is currently OpenJDK 26. The project is configured for Java 21 compatibility, and CI uses Temurin 21.
- GitHub connector could not create a PR for this repository, returning `403 Resource not accessible by integration`; create the PR manually or fix GitHub app write permissions.

## Near-Term Next Steps

1. Push `codex/phase-2-synthetic-data-generator`.
2. Open/merge the Phase 0/1 PR first.
3. Retarget or rebase Phase 2 onto `main` after Phase 0/1 merges.
4. Open the Phase 2 PR.

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
