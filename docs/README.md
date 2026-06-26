# InsureFlow AI Documentation

This folder contains project documentation that supports implementation, onboarding, and portfolio presentation.

## Start Here

1. [`../PROJECT_MEMORY.md`](../PROJECT_MEMORY.md) - living project memory and current status.
2. [`superpowers/plans/2026-06-24-insureflow-ai-master-build-plan.md`](superpowers/plans/2026-06-24-insureflow-ai-master-build-plan.md) - phase-by-phase master build plan.
3. [`../PROJECT_BLUEPRINT.md`](../PROJECT_BLUEPRINT.md) - full project blueprint copied into the repository during Phase 0.
4. [`superpowers/plans/2026-06-25-phase-3-4-policy-and-claims-workflow.md`](superpowers/plans/2026-06-25-phase-3-4-policy-and-claims-workflow.md) - implementation plan for the policy and FNOL workflow.
5. [`api/policy-claims-workflow.md`](api/policy-claims-workflow.md) - implemented API workflow for policy, coverage validation, FNOL, and claim operations.
6. [`superpowers/plans/2026-06-25-phase-5-rule-based-ai-triage-service.md`](superpowers/plans/2026-06-25-phase-5-rule-based-ai-triage-service.md) - implementation plan for the rule-based AI triage service.
7. [`api/ai-triage.md`](api/ai-triage.md) - implemented API workflow for AI triage scoring, persistence, and outage handling.
8. [`superpowers/plans/2026-06-25-phase-6-ml-triage-model-training.md`](superpowers/plans/2026-06-25-phase-6-ml-triage-model-training.md) - implementation plan for local ML triage model training.
9. [`ml/model-training.md`](ml/model-training.md) - Phase 6 local ML training workflow.
10. [`ml/severity-model-card.md`](ml/severity-model-card.md) - severity model card.
11. [`ml/fraud-risk-model-card.md`](ml/fraud-risk-model-card.md) - fraud-risk model card.
12. [`superpowers/plans/2026-06-26-phase-7-llm-document-intelligence.md`](superpowers/plans/2026-06-26-phase-7-llm-document-intelligence.md) - implementation plan for document intelligence.
13. [`api/document-intelligence.md`](api/document-intelligence.md) - Phase 7 document intelligence API contract.
14. [`superpowers/plans/2026-06-26-phase-8-rag-adjuster-assistant.md`](superpowers/plans/2026-06-26-phase-8-rag-adjuster-assistant.md) - implementation plan for the RAG adjuster assistant.
15. [`api/rag-assistant.md`](api/rag-assistant.md) - Phase 8 RAG assistant API contract.

## Planned Documentation Areas

- `architecture/` - system context, service architecture, data model, AI architecture, deployment.
- `domain/` - insurance glossary, claim lifecycle, policy lifecycle, Guidewire-inspired design.
- `api/` - backend, AI, and integration API contracts.
- `data/` - synthetic data strategy, data dictionary, generation rules.
- `ml/` - model cards, fraud/severity evaluation, governance.
- `rag/` - ingestion, chunking, retrieval, prompt design, evaluation.
- `demo/` - recruiter walkthrough, demo script, screenshots.
- `superpowers/plans/` - implementation plans used by Codex agents.

## Documentation Practice

Docs should be updated as part of each meaningful implementation step. Keep them practical: explain what exists, how to run it, why the design choice was made, and where the next agent should continue.
