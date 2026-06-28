# Phase 12 Cloud Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deployment-ready Docker, local app Compose, Azure Container Apps templates, deployment documentation, and validation scripts for InsureFlow AI.

**Architecture:** Package each runtime as a container, run the full product locally through a Compose `app` profile, and provide Azure Container Apps infrastructure as code for a later live deployment. Keep secrets externalized and validate cloud configuration without committing credentials.

**Tech Stack:** Docker, Docker Compose, Java 21/Spring Boot, Python 3.12/FastAPI/Uvicorn, Node/Vite/Nginx, Azure Bicep, GitHub Actions.

---

## File Map

- Create `backend/api/Dockerfile`: multi-stage Maven build and JRE runtime image for the Spring Boot API.
- Create `ai-services/triage-service/Dockerfile`: Python service runtime image for triage.
- Create `ai-services/document-intelligence-service/Dockerfile`: Python service runtime image for document intelligence.
- Create `ai-services/rag-service/Dockerfile`: Python service runtime image for RAG.
- Create `frontend/Dockerfile`: Node build plus Nginx static runtime.
- Create `frontend/nginx.conf`: SPA fallback and static asset server config.
- Modify `docker-compose.yml`: add app-profile services and health checks.
- Modify `.env.example`: add app and cloud deployment variables.
- Create `scripts/smoke-test-containers.sh`: local smoke test for health endpoints.
- Create `infra/azure/main.bicep`: Azure Container Apps deployment template.
- Create `infra/azure/main.parameters.example.json`: safe example parameters.
- Create `.github/workflows/deployment-validation.yml`: build Docker images and validate infra syntax.
- Create `docs/deployment/cloud-deployment.md`: runbook and Azure deployment guide.
- Modify `README.md`, `docs/README.md`, and `PROJECT_MEMORY.md`: document Phase 12 status and links.

## Task 1: Containerize The Backend

**Files:**
- Create: `backend/api/Dockerfile`

- [ ] **Step 1: Write build expectation**

Run before implementation:

```bash
docker build -f backend/api/Dockerfile -t insureflow-api:test backend/api
```

Expected: fails because `backend/api/Dockerfile` does not exist.

- [ ] **Step 2: Add the backend Dockerfile**

Create a multi-stage Dockerfile that builds with Maven and runs the generated Spring Boot jar on a JRE image:

```dockerfile
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /workspace
COPY pom.xml .
COPY src ./src
RUN mvn -q -DskipTests package

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /workspace/target/*.jar /app/insureflow-api.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/insureflow-api.jar"]
```

- [ ] **Step 3: Verify backend image build**

Run:

```bash
docker build -f backend/api/Dockerfile -t insureflow-api:test backend/api
```

Expected: image builds successfully.

## Task 2: Containerize AI Services

**Files:**
- Create: `ai-services/triage-service/Dockerfile`
- Create: `ai-services/document-intelligence-service/Dockerfile`
- Create: `ai-services/rag-service/Dockerfile`

- [ ] **Step 1: Write build expectations**

Run before implementation:

```bash
docker build -f ai-services/triage-service/Dockerfile -t insureflow-triage:test ai-services/triage-service
docker build -f ai-services/document-intelligence-service/Dockerfile -t insureflow-document-intelligence:test ai-services/document-intelligence-service
docker build -f ai-services/rag-service/Dockerfile -t insureflow-rag:test ai-services/rag-service
```

Expected: fail because the Dockerfiles do not exist.

- [ ] **Step 2: Add service Dockerfiles**

Use Python 3.12 slim images, install each service package, expose the correct port, and run Uvicorn:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY triage_service ./triage_service
RUN pip install --no-cache-dir .
EXPOSE 8001
CMD ["uvicorn", "triage_service.app:app", "--host", "0.0.0.0", "--port", "8001"]
```

Adapt the module name and port for:

- `document_intelligence.app:app` on port `8002`
- `rag_service.app:app` on port `8003`

- [ ] **Step 3: Verify AI image builds**

Run:

```bash
docker build -f ai-services/triage-service/Dockerfile -t insureflow-triage:test ai-services/triage-service
docker build -f ai-services/document-intelligence-service/Dockerfile -t insureflow-document-intelligence:test ai-services/document-intelligence-service
docker build -f ai-services/rag-service/Dockerfile -t insureflow-rag:test ai-services/rag-service
```

Expected: all images build successfully.

## Task 3: Containerize Frontend

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`

- [ ] **Step 1: Write build expectation**

Run before implementation:

```bash
docker build -f frontend/Dockerfile -t insureflow-frontend:test frontend
```

Expected: fails because `frontend/Dockerfile` does not exist.

- [ ] **Step 2: Add Nginx config**

Create `frontend/nginx.conf`:

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /assets/ {
        try_files $uri =404;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }
}
```

- [ ] **Step 3: Add frontend Dockerfile**

```dockerfile
FROM node:22-alpine AS build
WORKDIR /workspace
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/dist /usr/share/nginx/html
EXPOSE 80
```

- [ ] **Step 4: Verify frontend image build**

Run:

```bash
docker build -f frontend/Dockerfile -t insureflow-frontend:test frontend
```

Expected: image builds successfully.

## Task 4: Add Local App Compose Profile And Smoke Test

**Files:**
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Create: `scripts/smoke-test-containers.sh`

- [ ] **Step 1: Write failing compose validation**

Run:

```bash
docker compose --profile app config
```

Expected before changes: succeeds only for infra services and does not include app services.

- [ ] **Step 2: Add app services to compose**

Add services named:

- `api`
- `triage-service`
- `document-intelligence-service`
- `rag-service`
- `frontend`

Use `profiles: ["app"]`, local image builds, service health checks, and backend environment variables pointing to Compose service hostnames.

- [ ] **Step 3: Add smoke script**

Create `scripts/smoke-test-containers.sh` that:

- checks `http://localhost:8080/api/v1/health`
- checks `http://localhost:8001/health`
- checks `http://localhost:8002/health`
- checks `http://localhost:8003/health`
- checks `http://localhost:5173`

The script should use `curl --fail --silent --show-error`.

- [ ] **Step 4: Verify compose config and smoke script syntax**

Run:

```bash
docker compose --profile app config
bash -n scripts/smoke-test-containers.sh
```

Expected: both commands exit 0.

## Task 5: Add Azure Infrastructure Template

**Files:**
- Create: `infra/azure/main.bicep`
- Create: `infra/azure/main.parameters.example.json`

- [ ] **Step 1: Write validation expectation**

Run before implementation:

```bash
az bicep build --file infra/azure/main.bicep
```

Expected: fails because the template does not exist, or is skipped locally if Azure CLI is unavailable.

- [ ] **Step 2: Add Bicep template**

Define:

- Log Analytics workspace
- Container Apps managed environment
- Azure Database for PostgreSQL flexible server placeholder configuration
- Container Apps for frontend, API, triage, document intelligence, and RAG
- secret references for database password and JWT secret
- ingress enabled for frontend and API, internal ingress for AI services

- [ ] **Step 3: Add safe parameters example**

Use placeholder image names and non-secret parameter names in `infra/azure/main.parameters.example.json`.

- [ ] **Step 4: Verify Bicep build where available**

Run:

```bash
if command -v az >/dev/null 2>&1; then az bicep build --file infra/azure/main.bicep; else echo "Azure CLI not installed; skipping Bicep build"; fi
```

Expected: build succeeds when Azure CLI exists; otherwise command exits 0 with skip message.

## Task 6: Add Deployment Validation Workflow And Docs

**Files:**
- Create: `.github/workflows/deployment-validation.yml`
- Create: `docs/deployment/cloud-deployment.md`
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `PROJECT_MEMORY.md`

- [ ] **Step 1: Add GitHub Actions workflow**

Workflow should run on PRs touching deployment files and:

- build backend Docker image
- build frontend Docker image
- build three AI service Docker images
- run `docker compose --profile app config`
- run `bash -n scripts/smoke-test-containers.sh`
- run Bicep build only when Azure CLI setup succeeds

- [ ] **Step 2: Add deployment guide**

Document:

- local container demo startup
- smoke testing
- required environment variables
- Azure resource layout
- GitHub secrets needed for future deploys
- manual deployment command sequence
- rollback notes

- [ ] **Step 3: Update README, docs index, and memory**

Link the deployment guide and record that Phase 12 started on branch `cloud-deployment`.

- [ ] **Step 4: Run full verification**

Run:

```bash
./scripts/run-tests.sh
docker compose --profile app config
bash -n scripts/smoke-test-containers.sh
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 5: Commit and open PR**

```bash
git add .
git commit -m "chore: add cloud deployment configuration"
git push -u origin cloud-deployment
gh pr create --base main --head cloud-deployment --title "Phase 12: Cloud deployment readiness" --body-file /tmp/phase-12-pr-body.md
```

Create `/tmp/phase-12-pr-body.md` with:

```markdown
## Summary
- add Dockerfiles for backend, frontend, and AI services
- add local app Compose profile and smoke test script
- add Azure Container Apps Bicep template and deployment guide
- add deployment validation workflow

## Verification
- ./scripts/run-tests.sh
- docker compose --profile app config
- bash -n scripts/smoke-test-containers.sh
- git diff --check
```
