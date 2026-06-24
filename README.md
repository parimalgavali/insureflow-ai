# InsureFlow AI

InsureFlow AI is a cloud-native claims and policy intelligence platform inspired by modern P&C insurance core-system workflows.

It is a professional portfolio project for demonstrating insurance domain understanding, Java/Spring Boot backend engineering, AI/ML model serving, LLM/RAG document intelligence, auditability, and human-in-the-loop responsible AI.

## Status

Early foundation phase. The repository currently contains planning, documentation, local infrastructure, and backend schema bootstrapping work.

## Important Boundary

This is not an official Guidewire product, connector, implementation, or certified integration. It is a Guidewire-inspired portfolio project using synthetic and public data.

## Planned Capabilities

- Customer, policy, coverage, and claim domain model
- FNOL claim intake
- Policy and coverage validation
- Claim lifecycle and timeline
- Rule-based and ML-based AI triage
- LLM document extraction and claim summaries
- RAG-based adjuster assistant
- Human review and override workflow
- Audit logging and responsible AI governance
- Guidewire-style REST integration APIs
- Vue adjuster workbench

## Tech Stack

- Java 21
- Spring Boot 3
- PostgreSQL
- Flyway
- Python/FastAPI
- Vue 3
- Docker Compose
- GitHub Actions

## Local Infrastructure

```bash
docker compose up -d postgres rabbitmq
docker compose ps
```

## Backend

```bash
cd backend
mvn test
```

## Documentation

- [Project Memory](PROJECT_MEMORY.md)
- [Documentation Index](docs/README.md)
- [Master Build Plan](docs/superpowers/plans/2026-06-24-insureflow-ai-master-build-plan.md)

## Responsible AI Statement

AI outputs in this project are decision-support signals only. They must not be used for real claim approval, rejection, fraud accusation, legal advice, medical advice, or production insurance decisions.
