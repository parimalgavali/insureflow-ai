# InsureFlow AI Documentation

This folder contains implementation docs, portfolio docs, demo guides, and project memory for InsureFlow AI.

## Evaluator Quick Path

Start here if you are reviewing the project for a role, interview, or portfolio discussion:

1. [Root README](../README.md) - project overview, architecture, demo commands, and proof points.
2. [Five-minute demo script](demo/demo-script.md) - guided demo flow.
3. [Recruiter walkthrough](demo/recruiter-walkthrough.md) - plain-language project explanation.
4. [Interview talking points](demo/interview-talking-points.md) - deeper technical discussion prep.
5. [Project narrative](portfolio/project-narrative.md) - short, medium, and long story versions.
6. [Resume bullets](portfolio/resume-bullets.md) - role-aligned resume language.
7. [Responsible AI statement](ai/responsible-ai-statement.md) - AI limits, governance, and prohibited uses.

## Architecture And Domain

- [System context](architecture/system-context.md)
- [Service architecture](architecture/service-architecture.md)
- [Insurance glossary](domain/insurance-glossary.md)
- [Synthetic data strategy](data/synthetic-data-generation.md)
- [Data dictionary](data/data-dictionary.md)

## APIs And Workflows

- [Policy and claims workflow API](api/policy-claims-workflow.md)
- [AI triage API](api/ai-triage.md)
- [Document intelligence API](api/document-intelligence.md)
- [RAG assistant API](api/rag-assistant.md)
- [Integration APIs](api/integration-apis.md)
- [Integration API HTTP collection](api/collections/phase-10-integration-apis.http)
- [Security, audit, and governance](api/security-audit-governance.md)

## AI, ML, And Responsible AI

- [Responsible AI statement](ai/responsible-ai-statement.md)
- [Model training workflow](ml/model-training.md)
- [Severity model card](ml/severity-model-card.md)
- [Fraud-risk model card](ml/fraud-risk-model-card.md)
- [AI triage API](api/ai-triage.md)
- [Document intelligence API](api/document-intelligence.md)
- [RAG assistant API](api/rag-assistant.md)

## Frontend Demo

- [Adjuster workbench runbook](frontend/adjuster-workbench.md)
- [Five-minute demo script](demo/demo-script.md)
- [Screenshot checklist](demo/screenshot-checklist.md)

## Product Roadmap

- [Dynamic claims application roadmap](product/dynamic-claims-application-roadmap.md)

## Deployment, Quality, And Observability

- [Cloud deployment runbook](deployment/cloud-deployment.md)
- [Testing, quality, and observability](quality/testing-quality-observability.md)

Useful commands:

```bash
./scripts/run-tests.sh
./scripts/run-coverage.sh
./scripts/run-quality-gates.sh
docker compose --profile app --profile observability up -d --build
```

## Portfolio Package

- [Recruiter walkthrough](demo/recruiter-walkthrough.md)
- [Interview talking points](demo/interview-talking-points.md)
- [Screenshot checklist](demo/screenshot-checklist.md)
- [Project narrative](portfolio/project-narrative.md)
- [Resume bullets](portfolio/resume-bullets.md)

## Implementation History

- [Project memory](../PROJECT_MEMORY.md)
- [Full project blueprint](../PROJECT_BLUEPRINT.md)
- [Master build plan](superpowers/plans/2026-06-24-insureflow-ai-master-build-plan.md)

Phase plans and design specs:

- [Phase 0/1 repository and domain foundation](superpowers/plans/2026-06-24-phase-0-1-repository-and-domain-foundation.md)
- [Phase 2 synthetic data generator](superpowers/plans/2026-06-24-phase-2-synthetic-data-generator.md)
- [Phase 3/4 policy and claims workflow](superpowers/plans/2026-06-25-phase-3-4-policy-and-claims-workflow.md)
- [Phase 5 rule-based AI triage service](superpowers/plans/2026-06-25-phase-5-rule-based-ai-triage-service.md)
- [Phase 6 ML triage model training](superpowers/plans/2026-06-25-phase-6-ml-triage-model-training.md)
- [Phase 7 document intelligence](superpowers/plans/2026-06-26-phase-7-llm-document-intelligence.md)
- [Phase 8 RAG adjuster assistant](superpowers/plans/2026-06-26-phase-8-rag-adjuster-assistant.md)
- [Phase 9 adjuster workbench frontend](superpowers/plans/2026-06-26-phase-9-adjuster-workbench-frontend.md)
- [Phase 10 Guidewire-inspired integration APIs](superpowers/plans/2026-06-26-phase-10-guidewire-integration-apis.md)
- [Phase 11 security, audit, and governance](superpowers/plans/2026-06-28-phase-11-security-audit-governance.md)
- [Phase 12 cloud deployment readiness](superpowers/plans/2026-06-28-phase-12-cloud-deployment.md)
- [Phase 13 testing, quality, and observability](superpowers/plans/2026-06-29-phase-13-testing-quality-observability.md)
- [Phase 14 portfolio packaging design](superpowers/specs/2026-06-30-phase-14-portfolio-packaging-design.md)
- [Phase 14 portfolio packaging implementation plan](superpowers/plans/2026-06-30-phase-14-portfolio-packaging.md)
- [Dynamic claims application design](superpowers/specs/2026-06-30-dynamic-claims-application-design.md)
- [Dynamic claims application roadmap plan](superpowers/plans/2026-06-30-dynamic-claims-application-roadmap.md)
- [Phase 15 frontend routing shell](superpowers/plans/2026-06-30-phase-15-frontend-routing-shell.md)
- [Phase 16 live claim queue](superpowers/plans/2026-06-30-phase-16-live-claim-queue.md)
- [Phase 17 human review workflow](superpowers/plans/2026-07-01-phase-17-human-review-workflow.md)

## Documentation Practice

Docs should be practical and truthful. Explain what exists, how to run it, why the design choice was made, and what limitations matter. Keep the Guidewire-inspired boundary and responsible AI limitations visible in evaluator-facing material.
