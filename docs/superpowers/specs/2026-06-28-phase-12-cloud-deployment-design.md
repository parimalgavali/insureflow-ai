# Phase 12 Cloud Deployment Design

## Purpose

Phase 12 turns InsureFlow AI from a local multi-service project into a deployment-ready portfolio application. The goal is not to spend cloud money from this branch; it is to make the application packageable, runnable as containers, and ready for an Azure Container Apps deployment when credentials and subscription details are available.

## Recommended Approach

Use a two-layer deployment approach:

1. **Local container parity:** Add production-style Dockerfiles for the backend, frontend, and Python AI services. Extend Docker Compose with an application profile that runs PostgreSQL, the Spring Boot API, the triage service, document intelligence service, RAG service, and frontend web server.
2. **Azure-ready infrastructure:** Add Bicep templates and a deployment guide for Azure Container Apps, Azure Database for PostgreSQL, Log Analytics/Application Insights-style observability, and managed secrets. The templates should be reviewable and lintable without containing real credentials.

This keeps Phase 12 useful even before a live Azure subscription is connected and gives recruiters a concrete cloud deployment story.

## Scope

Phase 12 will add:

- Backend Docker image build using a multi-stage Maven/JRE image.
- Python AI service Docker images using package installation from each service directory.
- Frontend production image using Vite build output served by Nginx.
- Compose application profile for full local demo container startup.
- Health check and smoke test script for containerized services.
- Azure Bicep templates for deployment-ready infrastructure.
- GitHub Actions workflow that validates Docker builds and infrastructure templates without deploying.
- Deployment documentation and project memory updates.

Phase 12 will not add:

- Real Azure subscription IDs, tenant IDs, client secrets, or passwords.
- Mandatory live deployment from CI.
- Kubernetes manifests, because Azure Container Apps is enough for the portfolio path.
- Production-grade autoscaling policy tuning beyond conservative defaults.

## Architecture

The deployed shape remains intentionally simple:

- `insureflow-api` is the public backend API container.
- `insureflow-frontend` is the public static frontend container.
- `triage-service`, `document-intelligence-service`, and `rag-service` are internal service containers.
- PostgreSQL is externalized to Azure Database for PostgreSQL in cloud and a Compose Postgres container locally.
- Secrets are provided through environment variables locally and through Container Apps secrets in cloud.
- Logs are written to stdout/stderr for Docker and Azure log collection.

The backend keeps its current service-to-service HTTP contract with the triage service through `INSUREFLOW_AI_TRIAGE_BASE_URL`. Document intelligence and RAG services are independently containerized now, even if the backend does not yet call them directly.

## Configuration

Environment variables will be documented in `.env.example` and deployment docs:

- `SPRING_DATASOURCE_URL`
- `SPRING_DATASOURCE_USERNAME`
- `SPRING_DATASOURCE_PASSWORD`
- `INSUREFLOW_JWT_ISSUER`
- `INSUREFLOW_JWT_SECRET`
- `INSUREFLOW_AI_TRIAGE_BASE_URL`
- `VITE_API_BASE_URL`

Local container defaults can be safe demo values. Cloud templates must require secure values through parameters and secret references.

## Testing And Verification

Phase 12 verification should include:

- Unit and integration suite through `./scripts/run-tests.sh`.
- Docker image build validation for backend, frontend, and AI services.
- Compose config validation.
- Container smoke script against health endpoints after `docker compose --profile app up`.
- Azure Bicep syntax/build validation when Azure CLI is available.

Live Azure deployment is a documented manual step, not a required automated verification gate for this branch.

## Documentation

Add `docs/deployment/cloud-deployment.md` with:

- local container demo commands
- environment variables
- image build commands
- Azure resource overview
- GitHub Actions secret names for future deploy workflow
- manual Azure deployment steps
- smoke test checklist

Update README, docs index, and project memory so future sessions know Phase 12 is about deployment readiness first and live deployment second.
