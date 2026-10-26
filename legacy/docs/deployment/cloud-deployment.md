# Cloud Deployment

Phase 12 prepares InsureFlow AI for a public or semi-public portfolio deployment. The default target is Azure Container Apps because it fits the project shape: several containers, simple HTTP ingress, managed logs, external PostgreSQL, and secret-based configuration.

## Local Container Demo

Build and start the full local container stack:

```bash
docker compose --profile app up --build
```

In another terminal, run:

```bash
./scripts/smoke-test-containers.sh
```

Expected local URLs:

| Service | URL |
| --- | --- |
| Frontend | `http://localhost:5173` |
| Backend API | `http://localhost:8080/api/v1/health` |
| Triage service | `http://localhost:8001/health` |
| Document intelligence service | `http://localhost:8002/health` |
| RAG service | `http://localhost:8003/health` |

Stop the stack:

```bash
docker compose --profile app down
```

## Images

Build images individually:

```bash
docker build -f backend/api/Dockerfile -t insureflow-api:local .
docker build -f ai-services/triage-service/Dockerfile -t insureflow-triage:local ai-services/triage-service
docker build -f ai-services/document-intelligence-service/Dockerfile -t insureflow-document-intelligence:local ai-services/document-intelligence-service
docker build -f ai-services/rag-service/Dockerfile -t insureflow-rag:local ai-services/rag-service
docker build -f frontend/Dockerfile -t insureflow-frontend:local frontend
```

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `SPRING_DATASOURCE_URL` | JDBC URL for the backend database. |
| `SPRING_DATASOURCE_USERNAME` | Database username. |
| `SPRING_DATASOURCE_PASSWORD` | Database password. |
| `INSUREFLOW_JWT_ISSUER` | JWT issuer expected by the backend. |
| `INSUREFLOW_JWT_SECRET` | JWT HMAC signing secret. |
| `INSUREFLOW_AI_TRIAGE_BASE_URL` | Backend-to-triage service URL. |
| `VITE_API_BASE_URL` | Frontend API base URL for future deployed frontend wiring. |

Local defaults live in `.env.example`. Cloud values must be set through GitHub Actions secrets, Azure Container Apps secrets, or secure Azure deployment parameters.

## Azure Resource Shape

`infra/azure/main.bicep` defines:

- Log Analytics workspace
- Azure Container Apps managed environment
- Azure Database for PostgreSQL Flexible Server
- PostgreSQL database named `insureflow`
- Container App for frontend with public ingress
- Container App for backend API with public ingress
- Internal Container Apps for triage, document intelligence, and RAG
- secret references for PostgreSQL password and JWT secret

## Manual Azure Deployment

Build and push images to the registry you choose, then deploy the Bicep template:

```bash
az group create --name rg-insureflow-ai-dev --location eastus
az deployment group create \
  --resource-group rg-insureflow-ai-dev \
  --template-file infra/azure/main.bicep \
  --parameters @infra/azure/main.parameters.example.json \
  --parameters postgresAdminPassword="$POSTGRES_ADMIN_PASSWORD" jwtSecret="$INSUREFLOW_JWT_SECRET"
```

Use real image names and secure parameter values before running this against a live subscription.

## GitHub Actions Secrets For Future Deploys

Future live deployment automation should use:

| Secret | Purpose |
| --- | --- |
| `AZURE_CREDENTIALS` | Federated or service-principal credentials for Azure login. |
| `AZURE_RESOURCE_GROUP` | Target resource group. |
| `AZURE_LOCATION` | Target Azure region. |
| `POSTGRES_ADMIN_PASSWORD` | PostgreSQL administrator password. |
| `INSUREFLOW_JWT_SECRET` | Backend JWT signing secret. |
| `REGISTRY_LOGIN_SERVER` | Container registry login server. |

Phase 12 only validates deployment assets. It does not deploy automatically.

## Smoke Checklist

After a live deployment:

1. Open the frontend URL returned by the deployment.
2. Call `GET /api/v1/health` on the API URL.
3. Create a dev token with `POST /api/v1/auth/dev-token`.
4. Submit a sample FNOL claim.
5. Run AI triage on the claim.
6. Confirm audit and governance endpoints require auditor/admin roles.

## Rollback Notes

Container Apps support revision history. For a bad image rollout, switch traffic back to the previous healthy revision from the Azure portal or Azure CLI. Database migrations are forward-only in this project, so review Flyway migrations before deploying backend images that include schema changes.
