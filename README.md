# InsureFlow AI

InsureFlow AI is a cloud-native claims and policy intelligence platform inspired by modern P&C insurance core-system workflows.

It is a professional portfolio project for demonstrating insurance domain understanding, Java/Spring Boot backend engineering, AI/ML model serving, LLM/RAG document intelligence, auditability, and human-in-the-loop responsible AI.

## Status

The repository contains local infrastructure, synthetic data generation, backend business workflows for policy management and claims intake, the Phase 5 rule-based AI triage service, Phase 6 local ML triage model training, Phase 7 document intelligence service, and Phase 8 offline RAG adjuster assistant.

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

Swagger UI is available at `http://localhost:8080/swagger-ui.html` when the API is running.

The Phase 3/4 policy and claims workflow is documented in [docs/api/policy-claims-workflow.md](docs/api/policy-claims-workflow.md).

The Phase 5 rule-based AI triage workflow is documented in [docs/api/ai-triage.md](docs/api/ai-triage.md).

## AI Triage Service

```bash
cd ai-services/triage-service
python3 -m pip install -e ".[test]"
python3 -m pytest
python3 -m uvicorn triage_service.app:app --reload --port 8001
```

The backend calls the service at `insureflow.ai.triage.base-url`, which defaults to `http://localhost:8001`.

## ML Training

```bash
cd ml
python3 -m pip install -e ".[test]"
python3 -m pytest
python3 -m insureflow_ml.train --data-dir ../data/synthetic --artifacts-dir artifacts
```

Model training is documented in [docs/ml/model-training.md](docs/ml/model-training.md).

## Document Intelligence Service

```bash
cd ai-services/document-intelligence-service
python3 -m pip install -e ".[test]"
python3 -m pytest
python3 -m uvicorn document_intelligence.app:app --reload --port 8002
```

Document intelligence is documented in [docs/api/document-intelligence.md](docs/api/document-intelligence.md).

## RAG Assistant Service

```bash
cd ai-services/rag-service
python3 -m pip install -e ".[test]"
python3 -m pytest
python3 -m uvicorn rag_service.app:app --reload --port 8003
```

RAG assistant behavior is documented in [docs/api/rag-assistant.md](docs/api/rag-assistant.md).

## Synthetic Data

```bash
cd synthetic-data-generator
python3 -m venv ../.venv
../.venv/bin/python -m pip install ".[dev]"
../.venv/bin/python -m pytest
../.venv/bin/python -m generator --customers 500 --policies 650 --claims 200 --adjusters 25 --seed 42 --output-dir ../data/synthetic
```

## Documentation

- [Project Memory](PROJECT_MEMORY.md)
- [Documentation Index](docs/README.md)
- [Policy Claims Workflow API](docs/api/policy-claims-workflow.md)
- [AI Triage API](docs/api/ai-triage.md)
- [ML Model Training](docs/ml/model-training.md)
- [Document Intelligence API](docs/api/document-intelligence.md)
- [RAG Assistant API](docs/api/rag-assistant.md)
- [Master Build Plan](docs/superpowers/plans/2026-06-24-insureflow-ai-master-build-plan.md)

## Responsible AI Statement

AI outputs in this project are decision-support signals only. They must not be used for real claim approval, rejection, fraud accusation, legal advice, medical advice, or production insurance decisions.
