# Recruiter Walkthrough

InsureFlow AI is a public portfolio project for insurance technology roles. It is built to show that the candidate understands both software engineering and the realities of P&C claim operations.

## One-Minute Explanation

InsureFlow AI simulates an insurance claim workflow from policy validation through FNOL, claim triage, document intelligence, adjuster assistance, audit, human review, and integration APIs.

The project is Guidewire-inspired, but it is not an official Guidewire implementation or connector. It uses synthetic data and local services to demonstrate domain knowledge, Java/Spring Boot engineering, AI application design, cloud deployment readiness, and responsible AI thinking.

## Why This Is Relevant

Insurance platforms are not just CRUD systems. They need:

- strong domain models for policy and claims;
- auditable workflow history;
- integrations with core systems and downstream services;
- explainable AI decision support;
- human review and override controls;
- secure APIs and operational monitoring.

InsureFlow AI includes those concerns in one coherent project.

## What To Look For

### Insurance Domain Understanding

The project models customers, policies, coverages, claims, claim events, notes, documents, reserves, triage results, audit records, and integration events.

### Backend Engineering

The backend uses Java 21, Spring Boot, PostgreSQL, Flyway migrations, validation, JPA repositories, security, integration tests, Testcontainers, and OpenAPI/Swagger documentation.

### AI Application Engineering

The AI layer is split into clear FastAPI services:

- rule-based and ML-backed triage;
- document intelligence;
- RAG adjuster assistant.

The services use typed contracts, deterministic tests, and explicit fallback behavior.

### Responsible AI

The project treats AI as decision support. It includes model cards, synthetic data disclosure, reason codes, human review, audit logging, model/prompt registry views, and prohibited-use boundaries.

### Platform Readiness

The repository includes Dockerfiles, Docker Compose app profiles, Azure Container Apps templates, CI, security scanning, coverage, Prometheus, Grafana, and smoke tests.

## Best Fit Role Signals

- Java backend engineer for insurance or enterprise platforms.
- Insurance technology / Guidewire-adjacent implementation engineer.
- Full-stack engineer with domain workflow experience.
- AI application engineer who can integrate ML/LLM services responsibly.
- Cloud/platform engineer who understands deployment and observability basics.

## Suggested Review Path

1. Read the root `README.md`.
2. Open `docs/demo/demo-script.md`.
3. Review `docs/portfolio/project-narrative.md`.
4. Skim `docs/api/policy-claims-workflow.md`.
5. Skim `docs/ai/responsible-ai-statement.md`.
6. Check GitHub Actions for tests, quality, and security gates.

## Important Boundary

This project should be evaluated as a portfolio simulation. It does not process real insurance data, does not make production claim decisions, and does not claim affiliation with Guidewire.
