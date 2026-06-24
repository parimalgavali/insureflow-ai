# Phase 0/1 Repository And Domain Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the initial InsureFlow AI repository foundation, local infrastructure, Spring Boot backend skeleton, PostgreSQL schema, Flyway migrations, and baseline tests.

**Architecture:** Start as a pragmatic modular backend foundation: one Spring Boot API module backed by PostgreSQL and Flyway, with folders reserved for later backend modules, AI services, synthetic data, and frontend work. Keep Phase 0/1 focused on infrastructure, documentation, schema, and testable backend bootstrapping. Do not implement policy/claims business endpoints yet.

**Tech Stack:** Java 21, Spring Boot 3.3.x, Maven, PostgreSQL 16, Flyway, Spring Data JPA, Spring Validation, springdoc-openapi, JUnit 5, Testcontainers, Docker Compose, GitHub Actions.

---

## Working Branch

Use branch:

```bash
codex/project-memory-and-phase-plans
```

Before implementing, verify:

```bash
git status -sb
git branch --show-current
```

Expected branch:

```text
codex/project-memory-and-phase-plans
```

## Phase Boundaries

Build only Phase 0 and Phase 1.

Do not build:

- Synthetic data generator implementation.
- Policy CRUD endpoints.
- FNOL workflow.
- AI services.
- Frontend app.
- Security/JWT.
- Cloud deployment.

## File Structure To Create

```text
.
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── PROJECT_BLUEPRINT.md
├── PROJECT_MEMORY.md
├── README.md
├── docker-compose.yml
├── backend/
│   ├── README.md
│   ├── pom.xml
│   └── api/
│       ├── pom.xml
│       └── src/
│           ├── main/
│           │   ├── java/
│           │   │   └── com/
│           │   │       └── insureflow/
│           │   │           └── api/
│           │   │               ├── InsureFlowApiApplication.java
│           │   │               ├── config/
│           │   │               │   └── OpenApiConfig.java
│           │   │               ├── health/
│           │   │               │   └── HealthController.java
│           │   │               └── shared/
│           │   │                   └── api/
│           │   │                       └── ApiErrorResponse.java
│           │   └── resources/
│           │       ├── application.yml
│           │       └── db/
│           │           └── migration/
│           │               └── V1__create_core_insurance_schema.sql
│           └── test/
│               └── java/
│                   └── com/
│                       └── insureflow/
│                           └── api/
│                               ├── InsureFlowApiApplicationTests.java
│                               └── database/
│                                   └── FlywayMigrationTest.java
├── docs/
│   ├── README.md
│   ├── architecture/
│   │   ├── service-architecture.md
│   │   └── system-context.md
│   └── domain/
│       └── insurance-glossary.md
├── ai-services/
│   └── README.md
├── frontend/
│   └── README.md
├── synthetic-data-generator/
│   └── README.md
└── scripts/
    └── run-tests.sh
```

## Task 1: Repository Starter Files

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`
- Create: `PROJECT_BLUEPRINT.md`
- Modify: `PROJECT_MEMORY.md`

- [ ] **Step 1: Create `.gitignore`**

Use this content:

```gitignore
.DS_Store
.idea/
.vscode/
*.iml

.env
.env.*
!.env.example

target/
build/
out/

node_modules/
dist/
coverage/

.pytest_cache/
.ruff_cache/
__pycache__/
*.py[cod]
.venv/
venv/

data/raw/
data/processed/
data/synthetic/*.csv
data/synthetic/*.json

.worktrees/
worktrees/

*.log
```

- [ ] **Step 2: Create `.env.example`**

Use this content:

```dotenv
POSTGRES_DB=insureflow
POSTGRES_USER=insureflow
POSTGRES_PASSWORD=insureflow
POSTGRES_PORT=5432

RABBITMQ_DEFAULT_USER=insureflow
RABBITMQ_DEFAULT_PASS=insureflow
RABBITMQ_PORT=5672
RABBITMQ_MANAGEMENT_PORT=15672

SPRING_PROFILES_ACTIVE=local
SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/insureflow
SPRING_DATASOURCE_USERNAME=insureflow
SPRING_DATASOURCE_PASSWORD=insureflow
```

- [ ] **Step 3: Create initial `README.md`**

The README must include these sections:

```markdown
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
```

- [ ] **Step 4: Create `PROJECT_BLUEPRINT.md`**

Copy the full blueprint from:

```text
/Users/parimal_gavali/Developer/Guidewire/InsureFlow_AI_Complete_Project_Blueprint.md
```

into:

```text
PROJECT_BLUEPRINT.md
```

- [ ] **Step 5: Update `PROJECT_MEMORY.md`**

Add an entry under `Completed Work`:

```markdown
| 2026-06-24 | Started Phase 0/1 foundation branch. | Branch `codex/project-memory-and-phase-plans`. |
```

Add an entry under `Key Decisions`:

```markdown
| 2026-06-24 | Keep feature work off `main`; use `codex/` feature branches. | Keeps the public portfolio branch stable while implementation work is reviewed. |
```

- [ ] **Step 6: Verify starter files**

Run:

```bash
test -f README.md
test -f PROJECT_BLUEPRINT.md
test -f PROJECT_MEMORY.md
test -f .gitignore
test -f .env.example
```

Expected: no output and exit code `0`.

- [ ] **Step 7: Commit repository starter files**

Run:

```bash
git add .gitignore .env.example README.md PROJECT_BLUEPRINT.md PROJECT_MEMORY.md
git commit -m "docs: add repository foundation docs"
```

## Task 2: Local Infrastructure

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Create Docker Compose**

Use this content:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: insureflow-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-insureflow}
      POSTGRES_USER: ${POSTGRES_USER:-insureflow}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-insureflow}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-insureflow} -d ${POSTGRES_DB:-insureflow}"]
      interval: 10s
      timeout: 5s
      retries: 5

  rabbitmq:
    image: rabbitmq:3.13-management-alpine
    container_name: insureflow-rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_DEFAULT_USER:-insureflow}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_DEFAULT_PASS:-insureflow}
    ports:
      - "${RABBITMQ_PORT:-5672}:5672"
      - "${RABBITMQ_MANAGEMENT_PORT:-15672}:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  rabbitmq_data:
```

- [ ] **Step 2: Verify infrastructure starts**

Run:

```bash
docker compose up -d postgres rabbitmq
docker compose ps
```

Expected:

- `insureflow-postgres` is running or healthy.
- `insureflow-rabbitmq` is running or healthy.

- [ ] **Step 3: Commit local infrastructure**

Run:

```bash
git add docker-compose.yml
git commit -m "chore: add local infrastructure compose"
```

## Task 3: Documentation Skeleton

**Files:**
- Create: `docs/architecture/system-context.md`
- Create: `docs/architecture/service-architecture.md`
- Create: `docs/domain/insurance-glossary.md`
- Create: `backend/README.md`
- Create: `ai-services/README.md`
- Create: `frontend/README.md`
- Create: `synthetic-data-generator/README.md`

- [ ] **Step 1: Create architecture docs**

`docs/architecture/system-context.md` must explain:

- InsureFlow AI simulates P&C insurance policy and claims workflows.
- Primary users are adjusters, senior adjusters, underwriters, admins, customers, and external systems.
- AI supports triage, extraction, summarization, and grounded assistance.
- Humans make final decisions.

`docs/architecture/service-architecture.md` must document the planned modules:

- `backend/api` for initial Spring Boot API and schema.
- `ai-services` for FastAPI services.
- `frontend` for Vue workbench.
- `synthetic-data-generator` for generated relational/document data.
- PostgreSQL and RabbitMQ as local infrastructure.

- [ ] **Step 2: Create domain glossary**

`docs/domain/insurance-glossary.md` must define:

- Policy
- Coverage
- Deductible
- Claim
- FNOL
- Loss date
- Claim severity
- Fraud risk
- Litigation risk
- Subrogation
- Reserve
- Adjuster
- SIU

- [ ] **Step 3: Create module README files**

Each module README must include:

- Purpose.
- Current status.
- Planned responsibilities.
- Command placeholder only when the command already exists in this phase.

For `backend/README.md`, include:

```markdown
# Backend

Spring Boot backend foundation for InsureFlow AI.

## Current Status

Phase 0/1 creates the initial API application, Flyway schema, OpenAPI setup, and migration tests.

## Commands

```bash
mvn test
```
```

For `ai-services/README.md`, state that implementation starts in Phase 5.

For `frontend/README.md`, state that implementation starts after backend and AI contracts are stable.

For `synthetic-data-generator/README.md`, state that implementation starts in Phase 2.

- [ ] **Step 4: Commit documentation skeleton**

Run:

```bash
git add docs/architecture docs/domain backend/README.md ai-services/README.md frontend/README.md synthetic-data-generator/README.md
git commit -m "docs: add architecture and module skeletons"
```

## Task 4: Maven Backend Skeleton

**Files:**
- Create: `backend/pom.xml`
- Create: `backend/api/pom.xml`
- Create: `backend/api/src/main/java/com/insureflow/api/InsureFlowApiApplication.java`
- Create: `backend/api/src/main/java/com/insureflow/api/config/OpenApiConfig.java`
- Create: `backend/api/src/main/java/com/insureflow/api/health/HealthController.java`
- Create: `backend/api/src/main/java/com/insureflow/api/shared/api/ApiErrorResponse.java`
- Create: `backend/api/src/main/resources/application.yml`
- Create: `backend/api/src/test/java/com/insureflow/api/InsureFlowApiApplicationTests.java`

- [ ] **Step 1: Create parent Maven POM**

Use group ID:

```text
com.insureflow
```

Use artifact ID:

```text
insureflow-backend
```

Use Java:

```text
21
```

Include module:

```xml
<module>api</module>
```

- [ ] **Step 2: Create API Maven POM**

Include dependencies:

- `spring-boot-starter-web`
- `spring-boot-starter-validation`
- `spring-boot-starter-data-jpa`
- `flyway-core`
- `flyway-database-postgresql`
- `postgresql`
- `springdoc-openapi-starter-webmvc-ui`
- `spring-boot-starter-test`
- `testcontainers`
- `postgresql` Testcontainers module
- `junit-jupiter`

- [ ] **Step 3: Create Spring Boot application class**

Create `InsureFlowApiApplication.java`:

```java
package com.insureflow.api;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class InsureFlowApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(InsureFlowApiApplication.class, args);
    }
}
```

- [ ] **Step 4: Create OpenAPI config**

Create `OpenApiConfig.java` with an OpenAPI bean titled `InsureFlow AI API`, version `0.1.0`, and description `Guidewire-inspired claims and policy intelligence API`.

- [ ] **Step 5: Create health controller**

Create `HealthController.java`:

```java
package com.insureflow.api.health;

import java.time.Instant;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/health")
public class HealthController {

    @GetMapping
    public Map<String, Object> health() {
        return Map.of(
                "status", "UP",
                "service", "insureflow-api",
                "timestamp", Instant.now().toString());
    }
}
```

- [ ] **Step 6: Create shared error response record**

Create `ApiErrorResponse.java` with fields:

- `Instant timestamp`
- `int status`
- `String error`
- `String message`
- `String path`
- `String correlationId`

- [ ] **Step 7: Create application config**

Create `application.yml` with:

```yaml
spring:
  application:
    name: insureflow-api
  datasource:
    url: ${SPRING_DATASOURCE_URL:jdbc:postgresql://localhost:5432/insureflow}
    username: ${SPRING_DATASOURCE_USERNAME:insureflow}
    password: ${SPRING_DATASOURCE_PASSWORD:insureflow}
  jpa:
    hibernate:
      ddl-auto: validate
    open-in-view: false
  flyway:
    enabled: true

server:
  port: 8080

springdoc:
  swagger-ui:
    path: /swagger-ui.html
```

- [ ] **Step 8: Create context-load test**

Create `InsureFlowApiApplicationTests.java` with a `contextLoads` test using `@SpringBootTest`.

- [ ] **Step 9: Verify Maven skeleton**

Run:

```bash
cd backend
mvn test
```

Expected: application context loads after the migration file is added in Task 5. If run before Task 5, database/migration failures are expected.

## Task 5: Flyway Core Insurance Schema

**Files:**
- Create: `backend/api/src/main/resources/db/migration/V1__create_core_insurance_schema.sql`
- Create: `backend/api/src/test/java/com/insureflow/api/database/FlywayMigrationTest.java`

- [ ] **Step 1: Create migration file**

Create schema objects for:

- `customers`
- `policies`
- `coverages`
- `claims`
- `claim_documents`
- `claim_events`
- `adjusters`
- `ai_triage_results`
- `human_reviews`
- `audit_logs`
- `model_versions`
- `prompt_versions`

Requirements:

- Use UUID primary keys with `gen_random_uuid()`.
- Add `created_at` and `updated_at` where the entity can change.
- Use `jsonb` only for flexible payloads.
- Add indexes for:
  - `customers(email)`
  - `policies(policy_number)`
  - `policies(customer_id)`
  - `claims(claim_number)`
  - `claims(policy_id)`
  - `claims(status)`
  - `claim_events(claim_id, created_at)`
  - `audit_logs(entity_type, entity_id)`

The first SQL statement must enable:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

- [ ] **Step 2: Create migration test**

Create `FlywayMigrationTest.java` using Testcontainers PostgreSQL.

The test must:

- Start PostgreSQL 16.
- Apply Flyway migrations from `classpath:db/migration`.
- Query `information_schema.tables`.
- Assert all expected table names exist.

Expected table list:

```java
Set.of(
    "customers",
    "policies",
    "coverages",
    "claims",
    "claim_documents",
    "claim_events",
    "adjusters",
    "ai_triage_results",
    "human_reviews",
    "audit_logs",
    "model_versions",
    "prompt_versions"
)
```

- [ ] **Step 3: Verify migration**

Run:

```bash
cd backend
mvn test
```

Expected:

- `InsureFlowApiApplicationTests` passes.
- `FlywayMigrationTest` passes.

- [ ] **Step 4: Commit backend foundation**

Run:

```bash
git add backend
git commit -m "feat: add backend schema foundation"
```

## Task 6: CI And Test Script

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `scripts/run-tests.sh`

- [ ] **Step 1: Create GitHub Actions workflow**

Use this workflow:

```yaml
name: CI

on:
  push:
    branches:
      - main
      - "codex/**"
  pull_request:
    branches:
      - main

jobs:
  backend:
    name: Backend Tests
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Java
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "21"
          cache: maven

      - name: Run backend tests
        working-directory: backend
        run: mvn test
```

- [ ] **Step 2: Create test script**

Use this content:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -d "$ROOT_DIR/backend" ]; then
  (cd "$ROOT_DIR/backend" && mvn test)
fi
```

- [ ] **Step 3: Make script executable**

Run:

```bash
chmod +x scripts/run-tests.sh
```

- [ ] **Step 4: Verify CI-equivalent command**

Run:

```bash
./scripts/run-tests.sh
```

Expected: backend tests pass.

- [ ] **Step 5: Commit CI and test script**

Run:

```bash
git add .github/workflows/ci.yml scripts/run-tests.sh
git commit -m "ci: add backend test workflow"
```

## Task 7: Final Phase 0/1 Verification And Memory Update

**Files:**
- Modify: `PROJECT_MEMORY.md`

- [ ] **Step 1: Run full verification**

Run:

```bash
docker compose up -d postgres rabbitmq
docker compose ps
./scripts/run-tests.sh
git status -sb
```

Expected:

- PostgreSQL and RabbitMQ are running.
- Backend tests pass.
- Git status is clean before memory update.

- [ ] **Step 2: Update `PROJECT_MEMORY.md`**

Add completed work entry:

```markdown
| 2026-06-24 | Completed Phase 0/1 repository and backend foundation. | Local infra, backend skeleton, Flyway schema, CI, and tests added on `codex/project-memory-and-phase-plans`. |
```

Add known issue if GitHub CLI auth is still invalid:

```markdown
- Recheck `gh auth status` before pushing or opening PRs. Git remote sync worked previously, but CLI auth reported an invalid token in this environment.
```

- [ ] **Step 3: Commit memory update**

Run:

```bash
git add PROJECT_MEMORY.md
git commit -m "docs: record phase 0 and 1 foundation status"
```

- [ ] **Step 4: Push branch**

Run:

```bash
git push -u origin codex/project-memory-and-phase-plans
```

If push fails because GitHub CLI auth is invalid, report the exact error and stop.

## Final Output From Implementer

Return:

- Branch name.
- Commit SHAs created.
- Verification commands run.
- Test results.
- Any blockers.
- Whether the branch was pushed.

