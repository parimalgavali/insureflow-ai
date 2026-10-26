# Interview Talking Points

Use this guide to prepare concise technical explanations during interviews.

## Architecture

**Question:** Why split AI into separate FastAPI services instead of putting everything in Spring Boot?

**Answer:** The backend owns claim workflow, persistence, security, audit, and integration contracts. The Python services own AI-specific concerns: triage scoring, document intelligence, and retrieval. This keeps the Java domain model stable while allowing AI models, prompts, and retrieval logic to evolve behind typed HTTP contracts.

## Insurance Domain Model

**Question:** What insurance concepts does the project model?

**Answer:** It models customers, policies, coverages, claims, claim events, notes, documents, reserves, adjusters, AI triage results, audit logs, human reviews, and integration events. The workflow starts with policy and coverage context, then moves through FNOL, claim lifecycle, AI decision support, human review, and downstream integration.

## Guidewire Relevance

**Question:** Is this a Guidewire project?

**Answer:** No. It is Guidewire-inspired, not official. The relevance is in the surrounding patterns: policy and claim workflows, integration APIs, auditability, claim lifecycle thinking, and insurance domain language. It is intended to demonstrate readiness for Guidewire-adjacent insurance technology work without claiming product compatibility.

## AI Triage

**Question:** Why start with rules before ML?

**Answer:** Rules provide an explainable baseline and stable contract. They make reason codes and audit behavior clear before adding ML complexity. ML then augments severity and fraud-risk scoring while preserving fallback behavior when model artifacts are absent.

## ML Limitations

**Question:** Can these ML models be used in production?

**Answer:** No. They are trained on synthetic, rule-labeled data and exist to demonstrate training workflow, model packaging, metrics, model cards, and service integration. They are decision-support demos, not production insurance models.

## Document Intelligence

**Question:** How do you test LLM-like behavior locally?

**Answer:** The document intelligence service uses deterministic local providers that emit structured JSON. This makes extraction, retry, validation, missing-document checks, summaries, and audit behavior testable without external model calls or nondeterministic outputs.

## RAG

**Question:** How does the RAG assistant avoid unsupported answers?

**Answer:** It ingests synthetic claim documents, chunks them, retrieves relevant evidence, and returns source references. If evidence is missing, it reports that limitation instead of inventing an answer. That behavior is part of the service contract.

## Governance

**Question:** What responsible AI controls exist?

**Answer:** The project includes decision-support disclaimers, reason codes, human review and override enforcement, audit logging, correlation IDs, AI input/output snapshots, model cards, prompt/model registry views, and prohibited-use documentation.

## Security

**Question:** What security controls are implemented?

**Answer:** The backend includes JWT role-based access control, security filters, validation, structured audit logging, correlation IDs, and integration tests for access behavior. GitHub Actions also runs quality and Trivy filesystem scans.

## Deployment

**Question:** What does cloud deployment readiness mean here?

**Answer:** The project has Dockerfiles, a Compose app profile, smoke tests, environment configuration, and Azure Container Apps Bicep templates. The templates demonstrate cloud deployment structure, while the primary demo remains local and reproducible.

## Observability

**Question:** How do you know the system is healthy?

**Answer:** Spring Actuator exposes health and Prometheus metrics. Docker Compose can run Prometheus and Grafana with provisioned dashboards. The project also includes a load-smoke script and quality gates.

## Trade-Offs

**Question:** What would you improve next?

**Answer:** Next improvements would include replacing deterministic local LLM providers with a real provider adapter, adding real vector storage for RAG, expanding frontend API integration beyond demo data, adding more policy/claims edge cases, and deploying a public demo environment with seeded data.
