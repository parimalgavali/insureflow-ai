# InsureFlow AI — Complete Project Blueprint

**Project type:** Enterprise-grade portfolio project for Insurance Technology, Guidewire ecosystem readiness, Java/Spring Boot backend engineering, cloud-native architecture, and AI/ML/LLM applications.  
**Primary target market:** Europe, especially Germany and nearby Guidewire/insurance technology employers.  
**Target roles:** Guidewire Integration Developer, Insurance Technology Consultant, Java Backend Engineer for Insurance Platforms, Claims/Underwriting AI Application Engineer, Cloud Data/AI Engineer for Insurance.  
**Author:** Parimal Gavali  
**Document version:** 1.0  
**Last updated:** 2026-06-24  

---

## 0. How to Use This Document

This document is intended to be the **single source of truth** for building the project in a Codex-style development environment.

Before writing code, Codex or any developer should read this document fully and follow the implementation phases in order.

The project should not be treated as a small academic demonstration. It should be treated as a **professional portfolio product** that demonstrates:

1. Insurance domain understanding.
2. Guidewire-inspired system thinking.
3. Enterprise Java/Spring Boot backend engineering.
4. AI/ML model development and serving.
5. LLM/RAG-based document intelligence.
6. Cloud-native deployment and observability.
7. Responsible, auditable, human-in-the-loop AI.

The final project should be impressive enough that a Guidewire consultant, insurance technology recruiter, or Java/cloud engineering hiring manager can understand that the developer is serious about entering the insurance technology space.

---

## 1. Project Name

Recommended name:

# InsureFlow AI

Recommended subtitle:

> A cloud-native claims and policy intelligence platform inspired by modern P&C insurance core systems.

Alternative names:

- ClaimPilot AI
- InsureOps AI
- ClaimSphere AI
- PolicyClaim Intelligence Platform
- ClaimCore AI

Use **InsureFlow AI** unless there is a strong reason to rename later.

---

## 2. Executive Summary

InsureFlow AI is a cloud-native Property & Casualty insurance operations platform that simulates the workflows around modern core insurance systems such as Guidewire ClaimCenter and PolicyCenter.

The platform allows users to:

1. Create and manage insurance customers.
2. Create and manage insurance policies.
3. Configure coverages, deductibles, policy terms, and policy status.
4. Submit First Notice of Loss claims.
5. Validate claim coverage against active policies.
6. Predict claim severity using machine learning.
7. Predict fraud risk using machine learning.
8. Predict litigation/escalation risk using machine learning or hybrid rules.
9. Extract structured information from unstructured claim descriptions and documents using LLMs.
10. Summarize claim files for adjusters using LLMs.
11. Provide a RAG-based adjuster assistant for policy, claim, and guideline Q&A.
12. Route claims to appropriate adjuster queues.
13. Store audit logs for AI decisions and human overrides.
14. Expose Guidewire-style integration APIs for external systems.
15. Present an adjuster workbench frontend with actionable claim intelligence.

The purpose is not to copy Guidewire software. The purpose is to build a **Guidewire-relevant portfolio system** that proves the developer understands the surrounding insurance workflows, integrations, data, AI opportunities, and enterprise architecture patterns.

---

## 3. Why This Project Exists

### 3.1 Career Purpose

The developer already has experience in:

- Java/Spring Boot microservices.
- Enterprise banking systems.
- Testing and quality engineering.
- AI/ML projects.
- LLM/document summarization applications.
- Docker, CI/CD, and backend development.

This project connects those strengths to the insurance technology market.

The intended career message is:

> “I may not yet have professional Guidewire implementation experience, but I understand insurance workflows around policy and claims, I can build enterprise-grade Java integrations, and I can responsibly integrate AI/ML/LLM intelligence into insurance operations.”

### 3.2 Business Purpose

P&C insurers handle large volumes of claims. Claims teams must quickly answer questions such as:

- Was the policy active at the time of loss?
- Is this loss covered?
- Is the claim severe?
- Is there fraud risk?
- Is there litigation risk?
- Which documents are missing?
- Which adjuster should handle this claim?
- What is the next best action?
- What has happened in the claim file so far?

Many of these activities are manual, document-heavy, and time-consuming.

InsureFlow AI demonstrates how a modern insurance platform can combine:

- Core workflow systems.
- Structured data.
- Predictive ML.
- LLM document intelligence.
- Human-in-the-loop decision support.
- Auditability and governance.

### 3.3 Guidewire Relevance

Guidewire Cloud APIs are RESTful system APIs used by caller applications to request data from or initiate actions within InsuranceSuite applications, and the APIs are described through Swagger/OpenAPI-style definitions. This project should mirror that integration philosophy through clean REST APIs, OpenAPI documentation, and service-to-service integration patterns.

Guidewire claims solutions emphasize analytics around FNOL, severe claims identification, subrogation opportunities, litigation likelihood, and claim/policy visualization. InsureFlow AI should implement a simplified but realistic version of those ideas.

Guidewire’s AI positioning also emphasizes AI in quoting, underwriting, claims, and service. InsureFlow AI should therefore include both predictive ML and LLM-based assistance.

Important: This project must not claim to be an official Guidewire implementation, official Guidewire connector, or certified Guidewire product. It is a **Guidewire-inspired portfolio project**.

---

## 4. Non-Goals and Boundaries

The project should be ambitious, but boundaries are important.

### 4.1 This Project Is Not

- Not an official Guidewire product.
- Not a clone of Guidewire ClaimCenter, PolicyCenter, or BillingCenter.
- Not connected to a real insurer.
- Not using real customer PII.
- Not making legally binding claim decisions.
- Not replacing human adjusters.
- Not making automatic fraud accusations.
- Not providing insurance/legal advice to real customers.
- Not using private or illegally obtained insurance data.

### 4.2 This Project Is

- A professional portfolio project.
- A realistic insurance workflow simulation.
- A cloud-native enterprise backend project.
- An AI/ML/LLM integration showcase.
- A system that demonstrates domain thinking.
- A platform with synthetic and public datasets.
- A responsible AI decision-support system.

---

## 5. High-Level Product Vision

The product should answer this question:

> What would a modern claims intelligence layer look like if we built it around Guidewire-like policy and claim workflows using Java, cloud, ML, and LLMs?

The final user experience should be:

1. A customer submits a claim.
2. The system validates policy and coverage.
3. The system extracts structured fields from the customer’s claim description.
4. The ML triage engine predicts severity, fraud risk, and litigation risk.
5. The document intelligence service summarizes claim documents.
6. The system detects missing or inconsistent information.
7. The RAG assistant answers adjuster questions using policy/guideline/claim evidence.
8. A human adjuster reviews the claim and either accepts, modifies, or overrides the AI recommendations.
9. Every AI output and human action is stored in the audit log.

---

## 6. Primary User Personas

### 6.1 Customer

The customer reports a claim through a claim intake form.

Customer actions:

- Submit FNOL.
- Upload claim documents.
- Add loss description.
- View claim status.
- Respond to missing document requests.

In MVP, customer UI can be simple or simulated through API/Postman.

### 6.2 Claims Adjuster

The adjuster is the main user.

Adjuster actions:

- View claim queue.
- Open claim details.
- Review policy and coverage status.
- Review AI triage scores.
- Read AI-generated claim summary.
- Ask RAG assistant questions.
- Request missing documents.
- Approve, reject, escalate, or close claim.
- Override AI recommendations with reason.

### 6.3 Senior Adjuster

Senior adjuster handles complex claims.

Senior adjuster actions:

- Review high severity claims.
- Review high fraud risk claims.
- Handle litigation-prone claims.
- Approve reserve changes.
- Escalate to Special Investigation Unit.
- Review human override patterns.

### 6.4 Underwriter

Underwriter can review policy context and claim implications.

Underwriter actions:

- Review policy risk profile.
- See claim history.
- Ask underwriting guideline questions.
- Review risk indicators.

### 6.5 Admin

Admin manages reference data and users.

Admin actions:

- Manage adjusters.
- Configure claim queues.
- Configure product types.
- Configure coverage rules.
- Review audit logs.
- Manage model versions and prompt versions.

### 6.6 External System

External systems simulate Guidewire-style integration.

External system actions:

- Push policy updates.
- Pull claim status.
- Submit claim event.
- Sync documents.
- Receive claim triage event.

---

## 7. Core Business Domain

The domain is **Property & Casualty insurance**, with focus on motor/auto insurance first.

### 7.1 Insurance Concepts

#### Policy

A policy is a contract between insurer and customer.

Important fields:

- Policy number.
- Policyholder.
- Product type.
- Start date.
- End date.
- Status.
- Premium.
- Deductible.
- Coverage limit.
- Coverages.
- Exclusions.
- Endorsements.

#### Coverage

Coverage defines what is protected.

Examples:

- Collision coverage.
- Theft coverage.
- Fire coverage.
- Third-party liability.
- Personal injury.
- Comprehensive damage.

#### Deductible

Amount the customer pays before insurer pays.

#### Claim

A claim is a request for payment or service after a covered loss.

#### FNOL

First Notice of Loss. First report of a claim.

#### Loss Date

Date when the incident occurred.

#### FNOL Date

Date when the customer reported the incident.

#### Claim Severity

Expected seriousness/cost/complexity of the claim.

Severity can be:

- Low.
- Medium.
- High.

#### Fraud Risk

Likelihood that claim has suspicious indicators.

Important: The system must say **fraud risk**, not “fraud confirmed.”

#### Litigation Risk

Likelihood that the claim may become legally disputed or require legal review.

#### Subrogation

Potential for insurer to recover cost from a responsible third party.

Example: Another driver caused the accident.

#### Reserve

Amount set aside by insurer for expected claim payment.

#### Adjuster

Person who investigates and manages the claim.

#### SIU

Special Investigation Unit. Handles suspicious claims.

---

## 8. Functional Scope

### 8.1 MVP Functional Scope

The MVP must include:

1. Customer management.
2. Policy management.
3. Coverage management.
4. FNOL claim intake.
5. Claim lifecycle state machine.
6. Coverage validation.
7. ML severity scoring.
8. ML fraud risk scoring.
9. Rule-based litigation/subrogation indicators.
10. LLM claim description extraction.
11. LLM claim summary generation.
12. Document upload and metadata storage.
13. Missing document checklist.
14. Adjuster assignment.
15. Audit logging.
16. OpenAPI documentation.
17. Docker Compose local environment.
18. Basic Vue.js adjuster dashboard.
19. GitHub Actions CI.
20. README with architecture and demo guide.

### 8.2 Version 2 Functional Scope

After MVP, add:

1. RAG-based adjuster assistant.
2. Vector database with policy/guideline documents.
3. SHAP explainability.
4. Model version registry.
5. Prompt version registry.
6. Human override analytics.
7. Event-driven architecture with RabbitMQ or Kafka.
8. Cloud deployment.
9. Observability dashboards.
10. Role-based access control.

### 8.3 Version 3 Functional Scope

Advanced extensions:

1. Litigation risk model.
2. Subrogation prediction model.
3. Duplicate claim detection using embeddings.
4. Claim payment/reserve simulator.
5. SynthETIC simulator integration.
6. Multi-line insurance: motor, home, travel, property.
7. Bilingual documents: English/German or English/French.
8. Integration mock server for Guidewire-like APIs.
9. Load testing.
10. Production-like monitoring.

---

## 9. Technology Stack

### 9.1 Backend Stack

Recommended backend:

- Java 21.
- Spring Boot 3.x.
- Spring Web.
- Spring Data JPA.
- Spring Validation.
- Spring Security.
- PostgreSQL.
- Flyway for migrations.
- MapStruct for DTO mapping.
- Lombok optional.
- springdoc-openapi for Swagger UI.
- Testcontainers.
- JUnit 5.
- Mockito.
- Maven or Gradle.

Recommended choice: **Maven** if simplicity is preferred, **Gradle** if multi-module builds are desired.

Use Java/Spring Boot because:

- It matches enterprise insurance/banking systems.
- Guidewire ecosystem projects often involve Java/Gosu/JVM concepts.
- It fits the developer’s existing experience.
- It is strong for backend APIs, integrations, security, and testing.

Drawbacks:

- More boilerplate than Python/Node.
- Microservices add complexity.
- Requires disciplined architecture to avoid a messy monolith.

### 9.2 AI/ML Stack

Recommended AI stack:

- Python 3.11 or 3.12.
- FastAPI.
- Pydantic.
- pandas.
- numpy.
- scikit-learn.
- XGBoost or LightGBM.
- imbalanced-learn.
- SHAP.
- MLflow optional.
- joblib for model serialization.
- pytest.
- httpx for testing.
- ruff/black for formatting.

Use Python/FastAPI because:

- Python is best for ML workflows.
- FastAPI is simple and production-friendly.
- It integrates well with Java services over REST.
- It supports Pydantic schemas for strict AI output validation.

Drawbacks:

- Separate runtime from Java.
- Requires API contract management.
- Model serving must be versioned and monitored.

### 9.3 LLM/RAG Stack

Recommended:

- OpenAI API or Azure OpenAI for hosted LLM.
- Ollama/local model fallback for cost control.
- sentence-transformers for local embeddings or OpenAI embeddings.
- pgvector as vector store.
- LangChain or LlamaIndex optional.
- Prefer minimal custom RAG first before adding frameworks.

Use pgvector because:

- It keeps relational and vector data together.
- It reduces infrastructure complexity.
- It works well for MVP.
- It is easier than running separate vector DB.

Drawbacks:

- Dedicated vector DBs may scale better later.
- Need careful indexing and chunking strategy.

### 9.4 Frontend Stack

Recommended:

- Vue 3.
- Vite.
- TypeScript.
- Pinia.
- Vue Router.
- Tailwind CSS or PrimeVue.
- Axios.
- Chart.js or ECharts for risk visualizations.

Use Vue because:

- It matches existing project experience.
- It is productive for dashboards.
- It is easier to polish quickly.

Drawbacks:

- UI can consume time.
- Frontend should not distract from backend/AI quality.

### 9.5 Messaging Stack

Recommended MVP:

- RabbitMQ.

Advanced option:

- Kafka.

Use RabbitMQ first because:

- Easier setup.
- Good for event-driven workflow demonstration.
- Enough for a portfolio project.

Use Kafka later if:

- You want stronger streaming architecture.
- You want to show event sourcing or analytics pipelines.

### 9.6 Cloud Stack

Recommended primary cloud path for Europe/Germany:

- Azure Container Apps or Azure App Service.
- Azure Database for PostgreSQL.
- Azure Blob Storage.
- Azure Key Vault.
- Azure Monitor/Application Insights.
- GitHub Actions.

Alternative AWS path:

- AWS ECS/Fargate.
- Amazon RDS PostgreSQL.
- Amazon S3.
- AWS Secrets Manager.
- CloudWatch.
- GitHub Actions.

Use Azure if targeting German/European enterprise employers. Use AWS if you want broader market visibility.

### 9.7 DevOps Stack

- Docker.
- Docker Compose.
- GitHub Actions.
- Dependabot.
- OpenAPI generation.
- k6 or JMeter for load testing.
- Trivy for container vulnerability scanning.
- SonarQube optional.

### 9.8 Observability Stack

Local:

- Structured JSON logs.
- Correlation ID.
- Spring Actuator.
- Prometheus.
- Grafana.
- Loki optional.

Cloud:

- Application Insights for Azure.
- CloudWatch for AWS.
- OpenTelemetry optional.

---

## 10. Recommended System Architecture

### 10.1 MVP Architecture

For MVP, use a modular architecture that can run locally with Docker Compose.

```text
Frontend
  Vue.js Adjuster Workbench

Backend
  Spring Boot API Gateway / Backend-for-Frontend
  Spring Boot Policy Service
  Spring Boot Claims Service
  Spring Boot Assignment Service
  Spring Boot Audit Service

AI Layer
  FastAPI Triage Service
  FastAPI Document Intelligence Service

Data
  PostgreSQL
  pgvector extension
  Object storage emulator or local file storage
  RabbitMQ

DevOps
  Docker Compose
  GitHub Actions
  OpenAPI/Swagger
```

### 10.2 Recommended Repository Structure

```text
insureflow-ai/
├── README.md
├── PROJECT_BLUEPRINT.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── docs/
│   ├── architecture/
│   │   ├── system-context.md
│   │   ├── service-architecture.md
│   │   ├── data-model.md
│   │   ├── ai-architecture.md
│   │   └── deployment.md
│   ├── domain/
│   │   ├── insurance-glossary.md
│   │   ├── claims-lifecycle.md
│   │   ├── policy-lifecycle.md
│   │   └── guidewire-inspired-design.md
│   ├── api/
│   │   ├── policy-service-api.md
│   │   ├── claims-service-api.md
│   │   ├── ai-service-api.md
│   │   └── integration-api.md
│   ├── data/
│   │   ├── dataset-strategy.md
│   │   ├── synthetic-data-generation.md
│   │   ├── feature-engineering.md
│   │   └── data-dictionary.md
│   ├── ml/
│   │   ├── fraud-model.md
│   │   ├── severity-model.md
│   │   ├── litigation-model.md
│   │   ├── evaluation.md
│   │   └── model-governance.md
│   ├── rag/
│   │   ├── document-ingestion.md
│   │   ├── chunking-strategy.md
│   │   ├── retrieval-strategy.md
│   │   ├── prompt-design.md
│   │   └── rag-evaluation.md
│   └── demo/
│       ├── demo-script.md
│       ├── recruiter-walkthrough.md
│       └── screenshots.md
├── backend/
│   ├── pom.xml
│   ├── common/
│   ├── api-gateway/
│   ├── policy-service/
│   ├── claims-service/
│   ├── assignment-service/
│   ├── audit-service/
│   └── integration-service/
├── ai-services/
│   ├── pyproject.toml
│   ├── triage-service/
│   ├── document-intelligence-service/
│   ├── rag-service/
│   ├── shared/
│   └── tests/
├── data/
│   ├── raw/
│   ├── external/
│   ├── synthetic/
│   ├── processed/
│   └── sample/
├── synthetic-data-generator/
│   ├── pyproject.toml
│   ├── generator/
│   ├── templates/
│   ├── configs/
│   └── README.md
├── ml/
│   ├── notebooks/
│   ├── training/
│   ├── pipelines/
│   ├── models/
│   ├── evaluation/
│   └── README.md
├── frontend/
│   ├── package.json
│   ├── src/
│   ├── public/
│   └── README.md
├── infra/
│   ├── docker/
│   ├── k8s/
│   ├── azure/
│   ├── aws/
│   └── monitoring/
└── scripts/
    ├── bootstrap-local.sh
    ├── load-sample-data.sh
    ├── run-tests.sh
    └── generate-demo-data.sh
```

### 10.3 Microservices vs Modular Monolith

Recommended approach:

Start with **modular monolith or small set of services**, then split if needed.

For MVP:

- `policy-service`
- `claims-service`
- `ai-services`
- `frontend`

Do not over-engineer with 10 microservices on day one.

Better path:

1. Build working domain.
2. Add AI.
3. Add audit.
4. Add events.
5. Split services only when useful.

---

## 11. Core Domain Model

### 11.1 Main Entities

#### Customer

```text
customer_id UUID primary key
first_name
last_name
email
phone
date_of_birth
city
country
risk_segment
created_at
updated_at
```

#### Policy

```text
policy_id UUID primary key
policy_number unique
customer_id foreign key
product_type enum: MOTOR, HOME, TRAVEL, COMMERCIAL_PROPERTY
status enum: DRAFT, ACTIVE, LAPSED, CANCELLED, EXPIRED, RENEWED
start_date
end_date
premium_amount
currency
deductible_amount
coverage_limit_amount
created_at
updated_at
```

#### Coverage

```text
coverage_id UUID primary key
policy_id foreign key
coverage_type enum
coverage_limit
deductible
included boolean
terms_text
exclusion_text
created_at
updated_at
```

#### Claim

```text
claim_id UUID primary key
claim_number unique
policy_id foreign key
customer_id foreign key
loss_date
fnol_date
claim_type enum
loss_location_city
loss_location_country
loss_description text
estimated_damage_amount
currency
injury_reported boolean
third_party_involved boolean
police_report_available boolean
status enum
coverage_status enum
assigned_adjuster_id nullable
created_at
updated_at
```

#### ClaimStatus

Recommended status lifecycle:

```text
DRAFT
SUBMITTED
POLICY_VALIDATION_PENDING
COVERAGE_VERIFIED
COVERAGE_ISSUE
AI_TRIAGE_PENDING
AI_TRIAGED
ASSIGNED
IN_REVIEW
PENDING_CUSTOMER_DOCUMENTS
ESCALATED
APPROVED
REJECTED
PAYMENT_PENDING
PAID
CLOSED
REOPENED
```

#### ClaimDocument

```text
document_id UUID primary key
claim_id foreign key
document_type enum
file_name
storage_uri
mime_type
uploaded_by
uploaded_at
extracted_text_uri nullable
document_status enum
```

Document types:

```text
FNOL_STATEMENT
POLICY_DOCUMENT
REPAIR_INVOICE
POLICE_REPORT
MEDICAL_REPORT
DAMAGE_PHOTO_METADATA
CUSTOMER_EMAIL
ADJUSTER_NOTE
LEGAL_NOTICE
OTHER
```

#### ClaimEvent

```text
event_id UUID primary key
claim_id foreign key
event_type
event_payload JSONB
created_by
created_at
correlation_id
```

#### Adjuster

```text
adjuster_id UUID primary key
name
email
role enum: ADJUSTER, SENIOR_ADJUSTER, SIU_SPECIALIST, LEGAL_REVIEWER
specialization enum
max_active_claims
active_claim_count
available boolean
created_at
updated_at
```

#### AITriageResult

```text
triage_id UUID primary key
claim_id foreign key
model_version
prompt_version nullable
severity_score
severity_label
fraud_score
fraud_risk_label
litigation_score
litigation_risk_label
subrogation_potential
recommended_queue
human_review_required
reason_codes JSONB
raw_model_response JSONB
created_at
```

#### HumanReview

```text
review_id UUID primary key
claim_id foreign key
reviewer_id
review_action enum: ACCEPT_AI, OVERRIDE_AI, ESCALATE, REQUEST_INFO, APPROVE, REJECT
override_reason text nullable
review_notes text
created_at
```

#### AuditLog

```text
audit_id UUID primary key
entity_type
entity_id
action
actor_type
actor_id
before_state JSONB
after_state JSONB
correlation_id
created_at
```

#### PromptVersion

```text
prompt_version_id UUID primary key
prompt_name
version
prompt_template
model_name
temperature
created_at
active boolean
```

#### ModelVersion

```text
model_version_id UUID primary key
model_name
version
algorithm
training_dataset
metrics JSONB
artifact_uri
created_at
active boolean
```

---

## 12. Datasets and Data Strategy

This section is critical. The project must not rely on a single flat Kaggle CSV. A professional insurance platform needs relational data and document data.

### 12.1 Dataset Philosophy

Use three data layers:

1. **Public ML datasets** for fraud/severity model development.
2. **Synthetic enterprise insurance data** for backend workflows.
3. **Synthetic insurance documents** for LLM/RAG/document intelligence.

This combination solves the main problem: real insurance policy/claim data is private and difficult to obtain.

### 12.2 Public Dataset 1: Vehicle Insurance Fraud Detection

Use this as the primary public fraud ML dataset.

Source:

- Kaggle: `khusheekapoor/vehicle-insurance-fraud-detection`
- Dataset: automobile insurance “carclaims”
- Approximate size: 15,420 samples
- Legitimate claims: 14,497
- Fraudulent claims: 923
- Important property: high class imbalance
- License visible on Kaggle: CC0 Public Domain

Purpose:

- Train fraud classifier.
- Demonstrate imbalanced classification.
- Use AUROC/AUPRC, precision, recall, F1.
- Build fraud scoring endpoint.

Do not simply copy a Kaggle notebook. Use the dataset to train a model, then integrate that model into the claims workflow.

### 12.3 Public Dataset 2: Auto Insurance Claims Data

Use this as a secondary comparison dataset.

Source:

- Kaggle: `buntyshah/auto-insurance-claims-data`
- File: `insurance_claims.csv`
- Common use: fraud claims detection.

Purpose:

- Secondary fraud model validation.
- Feature engineering practice.
- Alternative data source if the first dataset is insufficient.

### 12.4 Public/Synthetic Document Dataset: RISC / RISCBAC

Use this for insurance-document NLP and RAG.

Source:

- RISC paper and dataset.
- RISC is an open-source Python package that generates realistic bilingual automobile insurance contracts.
- RISCBAC contains 10,000 French and English synthetic automobile insurance contracts.
- It supports NLP tasks such as summarization, question answering, simplification, translation, and NER.

Purpose:

- Policy document chunking.
- Coverage clause retrieval.
- Policy Q&A.
- Contract summarization.
- Document-grounded RAG responses.

This is highly relevant for Europe because it includes bilingual insurance contracts, although not German.

### 12.5 Public Simulator: SynthETIC

Use this for advanced claim lifecycle simulation.

Source:

- SynthETIC claim simulator.
- Open-source non-life insurance claim simulator.
- Can generate features of individual non-life insurance claims.
- Includes auto-liability-style default parameters.
- Supports settlement patterns, development patterns, inflation, dependencies, and claim evolution.

Purpose:

- Generate realistic claim payment/reserve timelines.
- Build advanced actuarial-style claim lifecycle data.
- Add reserve/payment history in Version 3.

This is optional for MVP, but impressive if integrated later.

### 12.6 Custom Synthetic Enterprise Data

This is mandatory.

Create a synthetic-data-generator module that produces relational insurance data.

Generate:

```text
customers.csv
policies.csv
coverages.csv
claims.csv
claim_documents.csv
claim_notes.csv
claim_events.csv
adjusters.csv
payments.csv
ai_triage_results.csv
audit_logs.csv
```

Target MVP volumes:

```text
customers: 5,000
policies: 6,500
coverages: 20,000
claims: 2,000
claim_documents: 5,000
claim_notes: 8,000
claim_events: 15,000
adjusters: 50
payments: 1,000
```

Target Version 2 volumes:

```text
customers: 50,000
policies: 70,000
claims: 25,000
documents: 75,000
events: 200,000
```

### 12.7 Synthetic Data Relationships

The data generator must ensure relational consistency:

```text
Customer 1..N Policy
Policy 1..N Coverage
Policy 0..N Claim
Claim 0..N ClaimDocument
Claim 0..N ClaimEvent
Claim 0..N Payment
Claim 0..1 AITriageResult
Adjuster 0..N Claim
```

### 12.8 Synthetic Claim Generation Rules

Create realistic rules.

#### Severity Label Generation

A claim is more likely high severity if:

- Estimated damage is high.
- Injury is reported.
- Third party is involved.
- Commercial vehicle/property involved.
- Police report exists or should exist.
- Claim type is fire, bodily injury, major collision, theft.
- Coverage limit is high.
- Loss location is high-risk.
- Claim description mentions injury, hospital, total loss, lawsuit, fire, flood.

Example severity scoring rule:

```text
severity_score = 0

if estimated_damage > 10000: +3
if estimated_damage > 25000: +5
if injury_reported: +5
if third_party_involved: +2
if claim_type in [FIRE, THEFT, BODILY_INJURY, MAJOR_COLLISION]: +3
if commercial_policy: +2
if loss_report_delay_days > 14: +1
if police_report_available == false and third_party_involved == true: +1

0-3: LOW
4-8: MEDIUM
9+: HIGH
```

#### Fraud Label Generation

A claim has higher fraud risk if:

- Policy age is very low.
- Claim reported shortly after policy start.
- Claim reported very late after loss.
- Prior claims count is high.
- Estimated damage is unusually high.
- Police report is missing.
- Claim description is inconsistent with document data.
- Loss location differs from customer location.
- Similar claim already exists.
- Customer has multiple claims in a short period.

Example fraud score rule:

```text
fraud_score = 0

if policy_age_days < 30: +4
if loss_report_delay_days > 21: +3
if prior_claims_count >= 3: +3
if estimated_damage > customer_segment_expected_amount * 3: +3
if police_report_available == false and claim_type in [THEFT, MAJOR_COLLISION]: +2
if invoice_amount > estimated_damage * 2: +2
if duplicate_similarity_score > 0.85: +3

0-3: LOW
4-7: MEDIUM
8+: HIGH
```

For supervised ML training, convert fraud risk to binary label:

```text
fraud_label = 1 if fraud_score >= threshold else 0
```

Use randomness to avoid perfectly deterministic labels.

#### Litigation Risk Generation

Litigation risk increases if:

- Injury reported.
- Third party involved.
- Disputed liability.
- Customer sentiment negative.
- High estimated damage.
- Legal notice document exists.
- Claim was previously rejected.
- Long cycle time.
- Multiple adjuster notes mention dispute.

Example:

```text
litigation_score = 0

if injury_reported: +4
if third_party_involved: +2
if estimated_damage > 20000: +2
if description contains ["lawyer", "court", "sue", "dispute", "responsible"]: +4
if claim_status == ESCALATED: +2
if missing critical documents: +1

0-2: LOW
3-6: MEDIUM
7+: HIGH
```

### 12.9 Synthetic Documents

Generate documents from templates.

Document templates:

1. FNOL statement.
2. Repair invoice.
3. Police report.
4. Medical note.
5. Customer email.
6. Adjuster note.
7. Policy document.
8. Coverage guideline.
9. Claim denial letter.
10. Missing document request letter.

Example FNOL statement template:

```text
On {loss_date}, I was driving my {vehicle_year} {vehicle_make} {vehicle_model}
near {loss_location_city}. Another vehicle {incident_description}. The estimated
damage is approximately {estimated_damage_amount} EUR. Injury reported: {injury_reported}.
Police report available: {police_report_available}.
```

Example repair invoice template:

```text
Repair Invoice
Invoice Number: {invoice_number}
Vehicle: {vehicle_make} {vehicle_model}
Repair Shop: {repair_shop}
Labor Cost: {labor_cost} EUR
Parts Cost: {parts_cost} EUR
Tax: {tax_amount} EUR
Total Amount: {invoice_total} EUR
```

### 12.10 Data Privacy

All generated data must be synthetic.

Rules:

- No real names from real people.
- No real policy numbers.
- No real claim numbers.
- No real addresses.
- No real license plates.
- No real emails.
- Use fake domains like `example-insurance.test`.
- Add README statement that data is synthetic.

---

## 13. AI/ML Design

The AI layer must be meaningful, not decorative.

### 13.1 AI/ML Purpose

The AI/ML layer supports:

1. Faster claim triage.
2. Early severe claim identification.
3. Fraud risk prioritization.
4. Litigation/escalation risk detection.
5. Structured extraction from unstructured text.
6. Claim file summarization.
7. Document-grounded adjuster assistance.
8. Better queue assignment.
9. Human decision support with explainability.

The AI must not make final binding decisions. Human review is required.

### 13.2 ML Model 1: Claim Severity Prediction

#### Problem Type

Multiclass classification.

Labels:

```text
LOW
MEDIUM
HIGH
```

#### Input Features

```text
policy_type
claim_type
estimated_damage_amount
injury_reported
third_party_involved
days_between_loss_and_fnol
policy_age_days
prior_claims_count
police_report_available
coverage_limit
deductible_amount
customer_risk_segment
loss_location_risk_score
commercial_policy_flag
```

#### Algorithms

Start with:

- Logistic Regression baseline.
- Random Forest.
- XGBoost or LightGBM.

Recommended production candidate:

- XGBoost or LightGBM.

#### Metrics

Use:

- Macro F1.
- Per-class precision.
- Per-class recall.
- Confusion matrix.
- Balanced accuracy.

Do not rely only on accuracy.

#### API Output

```json
{
  "claimId": "CLM-2026-00041",
  "modelName": "severity-xgboost",
  "modelVersion": "1.0.0",
  "severityLabel": "HIGH",
  "severityScore": 0.87,
  "classProbabilities": {
    "LOW": 0.03,
    "MEDIUM": 0.10,
    "HIGH": 0.87
  },
  "reasonCodes": [
    "INJURY_REPORTED",
    "HIGH_ESTIMATED_DAMAGE",
    "THIRD_PARTY_INVOLVED"
  ],
  "humanReviewRequired": true
}
```

### 13.3 ML Model 2: Fraud Risk Scoring

#### Problem Type

Binary classification or risk scoring.

Labels:

```text
0 = not fraudulent / no fraud reported
1 = fraud reported / suspicious
```

#### Input Features

```text
policy_age_days
claim_amount
prior_claims_count
loss_report_delay_days
claim_type
police_report_available
third_party_involved
injury_reported
invoice_claim_amount_ratio
customer_risk_segment
duplicate_similarity_score
loss_location_mismatch
```

#### Algorithms

Start with:

- Logistic Regression baseline.
- Random Forest.
- XGBoost/LightGBM.
- Isolation Forest as optional anomaly model.

Recommended:

- XGBoost for supervised fraud scoring.
- Isolation Forest as additional anomaly signal.

#### Class Imbalance Handling

Because fraud datasets are imbalanced:

- Use stratified train/test split.
- Use class weights.
- Try SMOTE carefully.
- Use precision-recall curves.
- Use AUPRC.
- Report precision at top-k.

Do not oversell performance if the dataset is small or synthetic.

#### API Output

```json
{
  "claimId": "CLM-2026-00041",
  "modelName": "fraud-xgboost",
  "modelVersion": "1.0.0",
  "fraudRiskScore": 0.74,
  "fraudRiskLevel": "HIGH",
  "reasonCodes": [
    "POLICY_AGE_LESS_THAN_30_DAYS",
    "LATE_FNOL",
    "MISSING_POLICE_REPORT",
    "HIGH_CLAIM_AMOUNT"
  ],
  "humanReviewRequired": true,
  "recommendedAction": "Route to SIU review queue"
}
```

### 13.4 ML Model 3: Litigation Risk Prediction

This can start rule-based and become ML later.

#### Problem Type

Binary or ordinal classification.

Labels:

```text
LOW
MEDIUM
HIGH
```

#### Features

```text
injury_reported
third_party_involved
disputed_liability
claim_amount
negative_sentiment_score
legal_keywords_present
missing_documents_count
days_open
prior_escalations
```

#### Algorithms

MVP:

- Rules + keyword NLP.

Version 2:

- Logistic Regression/Random Forest.
- Add text embeddings from claim notes.

#### API Output

```json
{
  "claimId": "CLM-2026-00041",
  "litigationRiskScore": 0.61,
  "litigationRiskLevel": "MEDIUM",
  "reasonCodes": [
    "INJURY_REPORTED",
    "THIRD_PARTY_INVOLVED",
    "DISPUTED_LIABILITY_LANGUAGE_DETECTED"
  ],
  "recommendedAction": "Assign to senior adjuster"
}
```

### 13.5 Duplicate Claim Detection

Use embeddings and similarity.

Inputs:

- Claim description.
- Customer ID.
- Loss date.
- Loss location.
- Claim type.
- Damage amount.

Approach:

1. Create embedding of normalized claim description.
2. Search recent claims from same customer or similar vehicle/location.
3. Calculate similarity score.
4. Flag duplicates above threshold.

Output:

```json
{
  "claimId": "CLM-2026-00041",
  "duplicateRisk": "POSSIBLE",
  "similarClaims": [
    {
      "claimNumber": "CLM-2026-00012",
      "similarityScore": 0.89,
      "reason": "Similar loss description and same policy within 14 days"
    }
  ]
}
```

### 13.6 Reason Codes

Every AI decision must include reason codes.

Reason codes should be deterministic and mapped from:

- Model explainability.
- Feature thresholds.
- SHAP values.
- Rules.

Examples:

```text
HIGH_ESTIMATED_DAMAGE
INJURY_REPORTED
THIRD_PARTY_INVOLVED
LATE_FNOL
POLICY_RECENTLY_STARTED
MISSING_POLICE_REPORT
INVOICE_AMOUNT_MISMATCH
PRIOR_CLAIMS_HIGH
LOSS_LOCATION_MISMATCH
DUPLICATE_CLAIM_SIMILARITY
```

### 13.7 Model Governance

Store:

- Model name.
- Model version.
- Training dataset version.
- Training date.
- Metrics.
- Feature list.
- Serialization format.
- Owner.
- Active flag.

Minimum artifact structure:

```text
ml/models/
├── fraud/
│   ├── 1.0.0/
│   │   ├── model.joblib
│   │   ├── feature_schema.json
│   │   ├── metrics.json
│   │   └── model_card.md
├── severity/
│   ├── 1.0.0/
│   │   ├── model.joblib
│   │   ├── feature_schema.json
│   │   ├── metrics.json
│   │   └── model_card.md
```

### 13.8 Model Card Template

Each model must have a model card.

```text
# Model Card: Fraud Risk Model v1.0.0

## Purpose
Predict fraud risk for motor insurance claims to support human triage.

## Training Data
Vehicle Insurance Fraud Detection public dataset + synthetic claims data.

## Intended Use
Decision support for routing claims to review queues.

## Not Intended Use
Automatic claim rejection or accusation of fraud.

## Features
[List features]

## Metrics
AUROC, AUPRC, precision, recall, F1.

## Limitations
Synthetic/public data may not represent real insurer data.

## Bias and Risk
May over-prioritize certain patterns due to generated labels.

## Human Oversight
All high-risk predictions require human review.
```

---

## 14. LLM and RAG Design

### 14.1 LLM Use Cases

Use LLMs for:

1. Claim description extraction.
2. Document field extraction.
3. Claim file summarization.
4. Missing document explanation.
5. Customer email draft generation.
6. RAG-based adjuster assistant.
7. Natural language explanation of model reason codes.

Do not use LLMs for:

- Final claim approval.
- Final claim rejection.
- Fraud accusation.
- Legal advice.
- Medical advice.

### 14.2 Claim Description Extraction

Input:

```text
"I was driving near Bielefeld when another car hit my rear bumper. The driver
left the scene. I have photos but no police report yet. Damage is around 4500 EUR."
```

Output schema:

```json
{
  "claimType": "MOTOR_COLLISION",
  "damageType": "REAR_BUMPER",
  "thirdPartyInvolved": true,
  "policeReportAvailable": false,
  "possibleHitAndRun": true,
  "estimatedDamageAmount": 4500,
  "injuryReported": false,
  "requiredDocuments": [
    "POLICE_REPORT",
    "DAMAGE_PHOTOS",
    "REPAIR_ESTIMATE"
  ]
}
```

Implementation requirements:

- Use Pydantic schema validation.
- Retry once if invalid JSON.
- Store raw prompt and response in audit table.
- Store prompt version.
- Never trust LLM extraction without validation rules.

### 14.3 Document Field Extraction

Supported documents:

- Repair invoice.
- Police report.
- Medical note.
- Policy document.
- Customer email.
- Adjuster note.

For repair invoice, extract:

```json
{
  "documentType": "REPAIR_INVOICE",
  "invoiceNumber": "INV-2026-10042",
  "repairShop": "Example Auto Repair GmbH",
  "laborCost": 1200,
  "partsCost": 2800,
  "taxAmount": 760,
  "totalAmount": 4760,
  "currency": "EUR"
}
```

### 14.4 Claim File Summary

The LLM should generate an adjuster summary.

Required summary sections:

1. Claim overview.
2. Policy and coverage status.
3. Incident details.
4. Documents received.
5. Missing documents.
6. AI risk scores.
7. Key inconsistencies.
8. Recommended next action.
9. Human review warning.

Example:

```text
Claim CLM-2026-00041 is a motor collision claim reported 6 days after the loss.
The policy was active at the time of loss and includes collision coverage with a
500 EUR deductible. The claimant reports rear bumper damage and possible
third-party involvement. The repair invoice amount is 8,400 EUR, significantly
above the initial estimate of 3,000 EUR. Police report is missing. Fraud risk is
medium-high and severity is high. Recommended next action: request police report
and assign to senior motor adjuster.
```

### 14.5 RAG Assistant

The RAG assistant answers questions using only available policy, claim, and guideline documents.

Example questions:

```text
Is this loss covered?
What documents are missing?
Why is the claim high risk?
What is the recommended next action?
Summarize the claim timeline.
Which exclusion might apply?
What should the adjuster check before approval?
```

### 14.6 RAG Data Sources

Use:

- Policy documents.
- Coverage guidelines.
- Claim notes.
- Uploaded documents.
- Adjuster notes.
- Synthetic company claims handling manual.
- RISC/RISCBAC contracts.

### 14.7 RAG Pipeline

```text
Document upload
→ Text extraction
→ Cleaning
→ Chunking
→ Embedding generation
→ Store chunks in pgvector
→ User asks question
→ Retrieve top-k relevant chunks
→ Construct grounded prompt
→ LLM answer
→ Return answer with source references
→ Store interaction in audit log
```

### 14.8 Chunking Strategy

Recommended:

- Chunk size: 500 to 900 tokens.
- Overlap: 80 to 150 tokens.
- Preserve section headings.
- Store metadata:

```text
document_id
claim_id
policy_id
document_type
section_title
page_number
chunk_index
created_at
```

### 14.9 RAG Answer Rules

The assistant must:

- Cite source document/chunk IDs.
- Say when evidence is missing.
- Avoid legal certainty.
- Avoid final approval/rejection.
- Recommend human review for ambiguity.
- Not hallucinate policy clauses.

Example safe answer:

```text
Based on the retrieved policy coverage section, collision damage appears to be
covered if the policy was active on the loss date. However, the police report is
missing and the repair invoice amount differs from the initial estimate. This
should be reviewed by an adjuster before any coverage decision is finalized.
```

### 14.10 Prompt Versioning

Every prompt must have:

- Prompt name.
- Prompt version.
- Prompt template.
- Model name.
- Temperature.
- JSON schema if applicable.
- Active flag.

Prompt examples:

```text
claim_description_extraction_v1
repair_invoice_extraction_v1
claim_summary_v1
rag_adjuster_assistant_v1
missing_documents_v1
customer_email_draft_v1
```

### 14.11 LLM Evaluation

Evaluate:

- JSON validity rate.
- Field extraction accuracy on generated test docs.
- Summary completeness.
- Hallucination rate.
- Source citation correctness.
- Refusal correctness when evidence missing.
- Latency.
- Cost.

Create test cases in:

```text
ai-services/tests/evaluation/
```

---

## 15. Backend Service Design

### 15.1 Policy Service

Responsibilities:

- Customer CRUD.
- Policy CRUD.
- Coverage CRUD.
- Policy status management.
- Coverage validation.

Important endpoints:

```http
POST /api/v1/customers
GET /api/v1/customers/{customerId}

POST /api/v1/policies
GET /api/v1/policies/{policyId}
GET /api/v1/policies/by-number/{policyNumber}
POST /api/v1/policies/{policyId}/activate
POST /api/v1/policies/{policyId}/cancel
POST /api/v1/policies/{policyId}/renew

GET /api/v1/policies/{policyId}/coverages
POST /api/v1/policies/{policyId}/coverages

POST /api/v1/policies/{policyId}/coverage-check
```

Coverage check request:

```json
{
  "lossDate": "2026-06-20",
  "claimType": "MOTOR_COLLISION",
  "estimatedDamageAmount": 4500,
  "country": "DE"
}
```

Coverage check response:

```json
{
  "policyId": "uuid",
  "policyNumber": "POL-2026-000001",
  "policyActiveOnLossDate": true,
  "coverageAvailable": true,
  "coverageType": "COLLISION",
  "deductibleAmount": 500,
  "coverageLimitAmount": 50000,
  "coverageStatus": "COVERED",
  "warnings": []
}
```

### 15.2 Claims Service

Responsibilities:

- FNOL intake.
- Claim lifecycle.
- Claim documents.
- Claim notes.
- Claim event timeline.
- Call Policy Service for coverage validation.
- Call AI Triage Service.
- Assign adjuster.

Important endpoints:

```http
POST /api/v1/claims/fnol
GET /api/v1/claims/{claimId}
GET /api/v1/claims/by-number/{claimNumber}
GET /api/v1/claims
PATCH /api/v1/claims/{claimId}/status
POST /api/v1/claims/{claimId}/documents
GET /api/v1/claims/{claimId}/documents
POST /api/v1/claims/{claimId}/notes
GET /api/v1/claims/{claimId}/timeline
POST /api/v1/claims/{claimId}/triage
POST /api/v1/claims/{claimId}/assign
POST /api/v1/claims/{claimId}/review
```

FNOL request:

```json
{
  "policyNumber": "POL-2026-000001",
  "lossDate": "2026-06-20",
  "claimType": "MOTOR_COLLISION",
  "lossLocationCity": "Bielefeld",
  "lossLocationCountry": "DE",
  "lossDescription": "Another car hit my rear bumper and left the scene.",
  "estimatedDamageAmount": 4500,
  "currency": "EUR",
  "injuryReported": false,
  "thirdPartyInvolved": true,
  "policeReportAvailable": false
}
```

FNOL response:

```json
{
  "claimId": "uuid",
  "claimNumber": "CLM-2026-000001",
  "status": "SUBMITTED",
  "coverageStatus": "VALIDATION_PENDING",
  "nextActions": [
    "Validate policy coverage",
    "Run AI triage",
    "Request police report"
  ]
}
```

### 15.3 AI Triage Service

FastAPI service.

Endpoints:

```http
POST /ai/v1/triage/score
POST /ai/v1/fraud/score
POST /ai/v1/severity/score
POST /ai/v1/litigation/score
GET /ai/v1/models
GET /ai/v1/health
```

Triage request:

```json
{
  "claimId": "CLM-2026-000001",
  "policy": {
    "policyType": "MOTOR",
    "policyAgeDays": 120,
    "coverageLimitAmount": 50000,
    "deductibleAmount": 500
  },
  "claim": {
    "claimType": "MOTOR_COLLISION",
    "estimatedDamageAmount": 4500,
    "injuryReported": false,
    "thirdPartyInvolved": true,
    "policeReportAvailable": false,
    "lossReportDelayDays": 6,
    "priorClaimsCount": 1
  }
}
```

Triage response:

```json
{
  "claimId": "CLM-2026-000001",
  "severity": {
    "label": "MEDIUM",
    "score": 0.62,
    "reasonCodes": ["THIRD_PARTY_INVOLVED", "MISSING_POLICE_REPORT"]
  },
  "fraud": {
    "riskLevel": "LOW",
    "score": 0.21,
    "reasonCodes": []
  },
  "litigation": {
    "riskLevel": "LOW",
    "score": 0.18,
    "reasonCodes": ["THIRD_PARTY_INVOLVED"]
  },
  "recommendedQueue": "MOTOR_ADJUSTER",
  "humanReviewRequired": true
}
```

### 15.4 Document Intelligence Service

Endpoints:

```http
POST /ai/v1/documents/extract
POST /ai/v1/documents/summarize
POST /ai/v1/documents/missing-check
POST /ai/v1/documents/compare
GET /ai/v1/documents/health
```

### 15.5 RAG Service

Endpoints:

```http
POST /ai/v1/rag/ingest
POST /ai/v1/rag/query
GET /ai/v1/rag/documents/{documentId}/chunks
```

RAG query request:

```json
{
  "claimId": "CLM-2026-000001",
  "question": "Is this loss covered under the policy?",
  "topK": 5
}
```

RAG query response:

```json
{
  "answer": "The loss appears potentially covered under collision coverage...",
  "sources": [
    {
      "documentId": "DOC-001",
      "chunkId": "CHUNK-008",
      "sectionTitle": "Collision Coverage",
      "pageNumber": 12
    }
  ],
  "confidence": "MEDIUM",
  "requiresHumanReview": true
}
```

### 15.6 Audit Service

Responsibilities:

- Store all important actions.
- Store AI requests/responses.
- Store prompt/model versions.
- Store human overrides.
- Provide audit search.

Endpoints:

```http
GET /api/v1/audit/entity/{entityType}/{entityId}
GET /api/v1/audit/claims/{claimId}
GET /api/v1/audit/ai-decisions/{claimId}
```

### 15.7 Integration Service

Guidewire-style integration simulation.

Endpoints:

```http
POST /integration/v1/policies/sync
POST /integration/v1/claims/create
POST /integration/v1/claims/{claimNumber}/status-update
POST /integration/v1/claims/{claimNumber}/reserve-update
GET /integration/v1/claims/{claimNumber}
POST /integration/v1/events/claim-triaged
```

Purpose:

- Demonstrate integration thinking.
- Show REST API contracts.
- Mirror system-to-system communication.

---

## 16. Event-Driven Design

### 16.1 Key Events

Use events to decouple workflow.

Events:

```text
ClaimSubmitted
PolicyCoverageValidated
CoverageIssueDetected
AITriageRequested
AITriageCompleted
ClaimAssigned
DocumentUploaded
DocumentExtracted
MissingDocumentsDetected
HumanReviewCompleted
ClaimEscalated
ClaimApproved
ClaimRejected
ClaimClosed
```

### 16.2 Event Payload Example

```json
{
  "eventId": "evt-uuid",
  "eventType": "ClaimSubmitted",
  "claimId": "uuid",
  "claimNumber": "CLM-2026-000001",
  "occurredAt": "2026-06-24T10:00:00Z",
  "correlationId": "corr-uuid",
  "payload": {
    "policyNumber": "POL-2026-000001",
    "claimType": "MOTOR_COLLISION"
  }
}
```

### 16.3 Recommended Event Flow

```text
FNOL submitted
→ ClaimSubmitted event
→ Policy Service validates coverage
→ PolicyCoverageValidated event
→ AI Triage Service scores claim
→ AITriageCompleted event
→ Assignment Service assigns queue
→ ClaimAssigned event
→ Adjuster reviews
→ HumanReviewCompleted event
```

---

## 17. Security Design

### 17.1 MVP Security

Minimum:

- Basic JWT authentication.
- Role-based authorization.
- Secure API endpoints.
- Environment variables for secrets.
- No secrets committed to GitHub.

Roles:

```text
CUSTOMER
ADJUSTER
SENIOR_ADJUSTER
UNDERWRITER
ADMIN
SYSTEM_INTEGRATION
```

### 17.2 Recommended Security Implementation

Use:

- Spring Security Resource Server.
- JWT tokens.
- Keycloak local container for Version 2.
- OAuth2/OIDC concepts.
- Role-based endpoint restrictions.

Example access rules:

```text
CUSTOMER: submit claim, view own claim
ADJUSTER: view assigned claims, add notes, request documents
SENIOR_ADJUSTER: review escalated claims
UNDERWRITER: view policy and risk context
ADMIN: manage data and users
SYSTEM_INTEGRATION: call integration APIs
```

### 17.3 AI Security

- Do not pass secrets to LLM prompts.
- Use synthetic data.
- Redact PII fields before LLM calls.
- Store prompt/response audit.
- Prevent prompt injection in RAG.
- Add system instructions that limit assistant behavior.
- Return “not enough evidence” when documents do not support answer.

---

## 18. Responsible AI Design

### 18.1 Human-in-the-Loop Principle

The AI never makes final claim decisions.

AI can recommend:

- Queue.
- Priority.
- Risk level.
- Missing documents.
- Next action.

Human must decide:

- Claim approval.
- Claim rejection.
- Fraud escalation.
- Payment.
- Legal action.

### 18.2 Auditability

Store:

- Input features.
- Model version.
- Prompt version.
- Output score.
- Reason codes.
- Raw response.
- Human decision.
- Override reason.

### 18.3 Explainability

Every score must be explainable.

Methods:

- Reason code mapping.
- SHAP values for tree models.
- Rule contributions.
- Retrieved sources for RAG answers.

### 18.4 Limitations Disclosure

README must say:

```text
This project is a portfolio simulation using public and synthetic datasets.
The AI outputs are decision-support signals only. They should not be used for
real claim approval, rejection, fraud accusation, legal advice, or production
insurance decisions.
```

---

## 19. Implementation Plan

Follow these phases in order.

---

# Phase 0: Repository and Development Setup

## Goal

Create the repository, documentation, tooling, and local environment.

## Tasks

1. Create GitHub repository `insureflow-ai`.
2. Add README.md.
3. Add PROJECT_BLUEPRINT.md.
4. Add `.gitignore`.
5. Add `.env.example`.
6. Add Docker Compose skeleton.
7. Create folder structure.
8. Add GitHub Actions skeleton.
9. Add initial architecture diagram in docs.

## Expected Output

- Repository compiles or at least boots empty services.
- Docker Compose starts PostgreSQL and RabbitMQ.
- README explains project purpose.

## Done Criteria

- `docker compose up` starts infrastructure.
- README has project overview.
- Folder structure matches this blueprint.

---

# Phase 1: Domain Model and Database

## Goal

Build the relational insurance domain.

## Tasks

1. Create PostgreSQL schema.
2. Add Flyway migrations.
3. Implement Customer entity.
4. Implement Policy entity.
5. Implement Coverage entity.
6. Implement Claim entity.
7. Implement ClaimDocument entity.
8. Implement ClaimEvent entity.
9. Implement Adjuster entity.
10. Implement AuditLog entity.
11. Add repositories.
12. Add DTOs.
13. Add validation.

## Expected Output

- Database schema exists.
- Spring Boot service can create/read core entities.
- Swagger UI shows endpoints.

## Done Criteria

- Unit tests for services.
- Integration tests with Testcontainers.
- Flyway migrations pass.

---

# Phase 2: Synthetic Data Generator

## Goal

Generate realistic synthetic insurance data.

## Tasks

1. Create Python generator module.
2. Generate customers.
3. Generate policies.
4. Generate coverages.
5. Generate claims.
6. Generate claim documents metadata.
7. Generate claim notes.
8. Generate claim events.
9. Generate adjusters.
10. Generate labels for severity/fraud/litigation.
11. Export CSV and JSON.
12. Add loader script into PostgreSQL.

## Expected Output

Generated files:

```text
data/synthetic/customers.csv
data/synthetic/policies.csv
data/synthetic/coverages.csv
data/synthetic/claims.csv
data/synthetic/claim_documents.csv
data/synthetic/claim_notes.csv
data/synthetic/claim_events.csv
data/synthetic/adjusters.csv
```

## Done Criteria

- Data loads into PostgreSQL.
- Foreign keys are valid.
- Generated data has realistic distributions.
- README explains data generation rules.

---

# Phase 3: Policy Service

## Goal

Implement policy and coverage logic.

## Tasks

1. Create policy CRUD endpoints.
2. Create coverage CRUD endpoints.
3. Create policy status transitions.
4. Implement coverage check.
5. Add policy lifecycle events.
6. Add tests.

## Business Rules

Coverage check must validate:

- Policy exists.
- Policy was active on loss date.
- Claim type maps to included coverage.
- Loss amount is within coverage limit.
- Deductible is available.
- Exclusions are considered.

## Done Criteria

- Coverage check returns clear status.
- Tests cover active, expired, cancelled, excluded, over-limit cases.

---

# Phase 4: Claims Service and FNOL

## Goal

Implement claim intake and lifecycle.

## Tasks

1. Create FNOL endpoint.
2. Generate claim number.
3. Store claim.
4. Validate policy number.
5. Call coverage check.
6. Store claim event timeline.
7. Add claim status transitions.
8. Add claim notes.
9. Add document metadata.
10. Add tests.

## Done Criteria

- Claim can be submitted.
- Policy coverage is checked.
- Claim status progresses correctly.
- Claim timeline is visible.

---

# Phase 5: AI Triage Service — Rules First

## Goal

Build AI triage API with deterministic rules before ML.

## Tasks

1. Create FastAPI triage service.
2. Define Pydantic request/response schemas.
3. Implement rule-based severity scoring.
4. Implement rule-based fraud scoring.
5. Implement rule-based litigation scoring.
6. Return reason codes.
7. Integrate Claims Service with AI service.
8. Store triage result in database.
9. Add tests.

## Why Rules First

Rules give a working baseline.
They help validate domain logic.
They provide explainable outputs.
They make integration easier before ML model training.

## Done Criteria

- Claim triage endpoint returns severity/fraud/litigation.
- Claims service stores AI result.
- Adjuster can see reason codes.

---

# Phase 6: ML Model Training

## Goal

Train fraud and severity models.

## Tasks

1. Download public fraud dataset.
2. Add dataset README and source/license notes.
3. Create preprocessing pipeline.
4. Train baseline Logistic Regression.
5. Train Random Forest.
6. Train XGBoost/LightGBM.
7. Evaluate models.
8. Save best model.
9. Create model card.
10. Add inference pipeline.
11. Replace or augment rule-based score with ML output.

## Fraud Metrics

Report:

- AUROC.
- AUPRC.
- Precision.
- Recall.
- F1.
- Confusion matrix.
- Precision at top 5% highest-risk claims.

## Severity Metrics

Report:

- Macro F1.
- Balanced accuracy.
- Per-class recall.
- Confusion matrix.

## Done Criteria

- Model artifact saved.
- Model card written.
- Triage API uses model.
- Inference tests pass.

---

# Phase 7: LLM Document Intelligence

## Goal

Add LLM-based extraction and summarization.

## Tasks

1. Create document intelligence FastAPI service.
2. Add prompt templates.
3. Add Pydantic schemas.
4. Implement claim description extraction.
5. Implement repair invoice extraction.
6. Implement claim summary generation.
7. Implement missing document detection.
8. Store prompt version.
9. Store raw LLM response.
10. Add tests with synthetic documents.

## Done Criteria

- LLM extracts structured JSON.
- Invalid JSON is handled.
- Summary is generated.
- Missing documents are listed.
- Outputs are audited.

---

# Phase 8: RAG Assistant

## Goal

Add document-grounded adjuster assistant.

## Tasks

1. Enable pgvector.
2. Create document_chunks table.
3. Implement document ingestion.
4. Implement chunking.
5. Generate embeddings.
6. Store chunks.
7. Implement retrieval.
8. Implement grounded answer generation.
9. Return sources.
10. Add hallucination/evidence tests.

## Done Criteria

- User can ask questions over policy/claim documents.
- Answers include sources.
- Assistant says when evidence is missing.

---

# Phase 9: Adjuster Workbench Frontend

## Goal

Build recruiter-friendly UI.

## Pages

1. Login page.
2. Claim queue.
3. Claim detail.
4. Policy detail.
5. AI triage panel.
6. Document panel.
7. RAG assistant panel.
8. Claim timeline.
9. Human review/override modal.
10. Admin/audit view.

## Claim Detail Layout

```text
Header:
  Claim number, status, priority

Left panel:
  Customer and policy details

Center:
  Claim description, documents, timeline

Right panel:
  AI scores, reason codes, recommended action

Bottom:
  Notes, human review, RAG assistant
```

## Done Criteria

- Recruiter can understand project from UI.
- Dashboard shows AI output clearly.
- Human override is visible.

---

# Phase 10: Integration APIs

## Goal

Demonstrate Guidewire-style system integration.

## Tasks

1. Create integration controller.
2. Add policy sync endpoint.
3. Add claim create endpoint.
4. Add claim status update endpoint.
5. Add reserve update endpoint.
6. Add event webhook simulation.
7. Document OpenAPI.
8. Add Postman collection.

## Done Criteria

- Integration APIs are documented.
- README explains Guidewire-inspired integration design.
- API responses are consistent.

---

# Phase 11: Security, Audit, and Governance

## Goal

Make the project enterprise-grade.

## Tasks

1. Add JWT auth.
2. Add roles.
3. Add audit logging aspect/interceptor.
4. Add AI decision audit.
5. Add human override reason requirement.
6. Add correlation IDs.
7. Add structured logs.
8. Add basic rate limiting optional.

## Done Criteria

- Protected endpoints.
- Audit logs visible.
- AI outputs traceable.

---

# Phase 12: Cloud Deployment

## Goal

Deploy MVP publicly or semi-publicly.

## Azure Path

Use:

- Azure Container Apps.
- Azure Database for PostgreSQL.
- Azure Blob Storage.
- Azure Key Vault.
- GitHub Actions.
- Azure Monitor/Application Insights.

## AWS Path

Use:

- ECS Fargate.
- RDS PostgreSQL.
- S3.
- Secrets Manager.
- CloudWatch.
- GitHub Actions.

## Done Criteria

- Backend deployed.
- AI service deployed.
- Frontend deployed.
- Database deployed.
- Environment variables secure.
- Demo URL available.

---

# Phase 13: Testing and Quality

## Backend Tests

- Unit tests.
- Integration tests.
- Testcontainers.
- Controller tests.
- Repository tests.
- Service tests.

## AI Tests

- Schema validation tests.
- Model inference tests.
- Prompt response tests.
- RAG retrieval tests.
- Evaluation tests.

## Frontend Tests

- Component tests.
- API mock tests.
- E2E tests optional.

## Load Tests

Use k6 or JMeter.

Test:

- FNOL submission.
- Claim triage.
- Claim queue loading.
- RAG query.

## Quality Gates

Minimum:

```text
Backend unit/integration coverage: 70%+
Critical service coverage: 85%+
AI schema tests: mandatory
Docker build: mandatory
No secrets in repo
Swagger docs available
```

---

# Phase 14: Documentation and Portfolio Packaging

## Required Documentation

1. README.md.
2. Architecture diagram.
3. Dataset strategy.
4. Data dictionary.
5. API documentation.
6. ML model cards.
7. RAG design.
8. Responsible AI statement.
9. Deployment guide.
10. Demo script.

## README Structure

```text
# InsureFlow AI

## Problem
P&C insurers handle high claim volumes and document-heavy workflows.

## Solution
InsureFlow AI provides claims/policy workflow simulation with AI triage and
LLM-based document intelligence.

## Features
- FNOL intake
- Policy and coverage validation
- ML severity/fraud scoring
- LLM document extraction
- RAG adjuster assistant
- Human-in-the-loop review
- Audit logging
- Guidewire-style integration APIs

## Architecture
[diagram]

## Tech Stack
Java, Spring Boot, Python, FastAPI, PostgreSQL, pgvector, Vue, Docker, Azure/AWS.

## Demo
[video]

## Responsible AI
AI outputs are decision-support only.
```

---

## 20. Coding Standards

### 20.1 Backend

Use package structure:

```text
com.insureflow.policy
com.insureflow.claims
com.insureflow.audit
com.insureflow.integration
com.insureflow.common
```

Each service should use:

```text
controller
service
repository
domain/entity
dto
mapper
exception
config
```

### 20.2 API Design

Rules:

- Use `/api/v1`.
- Use nouns, not verbs.
- Use proper HTTP methods.
- Use consistent error response.
- Use correlation ID.
- Use pagination for list endpoints.
- Use OpenAPI descriptions.

Error response:

```json
{
  "timestamp": "2026-06-24T10:00:00Z",
  "status": 400,
  "error": "Bad Request",
  "message": "Policy is not active on loss date",
  "path": "/api/v1/claims/fnol",
  "correlationId": "corr-uuid"
}
```

### 20.3 Python AI Code

Use structure:

```text
triage_service/
├── app/
│   ├── main.py
│   ├── api/
│   ├── schemas/
│   ├── services/
│   ├── models/
│   ├── reason_codes/
│   └── config.py
├── tests/
└── README.md
```

Rules:

- Use Pydantic for request/response.
- Validate model input schema.
- Log model version.
- Do not hardcode secrets.
- Add pytest tests.
- Use type hints.

### 20.4 Database

Rules:

- Use UUID primary keys.
- Use created_at and updated_at.
- Use enum tables or checked enums.
- Use JSONB only where flexible data is needed.
- Use indexes on policy number, claim number, status.
- Use Flyway migrations.

---

## 21. API and Data Contracts

### 21.1 Claim Triage Contract

The Java Claims Service and Python AI Service must share a stable contract.

Request:

```json
{
  "claimId": "string",
  "claimNumber": "string",
  "policyFeatures": {
    "policyType": "MOTOR",
    "policyAgeDays": 120,
    "coverageLimitAmount": 50000,
    "deductibleAmount": 500,
    "priorClaimsCount": 1
  },
  "claimFeatures": {
    "claimType": "MOTOR_COLLISION",
    "estimatedDamageAmount": 4500,
    "injuryReported": false,
    "thirdPartyInvolved": true,
    "policeReportAvailable": false,
    "lossReportDelayDays": 6
  },
  "textFeatures": {
    "lossDescription": "string"
  }
}
```

Response:

```json
{
  "claimId": "string",
  "modelVersion": "string",
  "severity": {
    "label": "LOW|MEDIUM|HIGH",
    "score": 0.0,
    "reasonCodes": []
  },
  "fraud": {
    "riskLevel": "LOW|MEDIUM|HIGH",
    "score": 0.0,
    "reasonCodes": []
  },
  "litigation": {
    "riskLevel": "LOW|MEDIUM|HIGH",
    "score": 0.0,
    "reasonCodes": []
  },
  "recommendedQueue": "string",
  "humanReviewRequired": true
}
```

### 21.2 Reason Code Contract

Create central list:

```text
HIGH_ESTIMATED_DAMAGE
INJURY_REPORTED
THIRD_PARTY_INVOLVED
LATE_FNOL
MISSING_POLICE_REPORT
POLICY_RECENTLY_STARTED
PRIOR_CLAIMS_HIGH
INVOICE_AMOUNT_MISMATCH
LOSS_LOCATION_MISMATCH
LEGAL_KEYWORDS_DETECTED
DUPLICATE_CLAIM_SIMILARITY
COVERAGE_LIMIT_EXCEEDED
POLICY_NOT_ACTIVE_ON_LOSS_DATE
```

---

## 22. Dashboard Requirements

### 22.1 Claim Queue

Columns:

```text
Claim Number
Policy Number
Claim Type
Status
Severity
Fraud Risk
Litigation Risk
Assigned Queue
FNOL Date
Age
```

Filters:

```text
Status
Severity
Fraud risk
Assigned adjuster
Claim type
Human review required
```

### 22.2 Claim Detail

Show:

- Claim overview.
- Policy coverage.
- AI triage.
- Reason codes.
- Documents.
- Timeline.
- Notes.
- RAG assistant.
- Human action buttons.

### 22.3 AI Triage Panel

Show:

```text
Severity: HIGH, 87%
Fraud risk: MEDIUM, 62%
Litigation risk: LOW, 21%
Recommended queue: Senior Motor Adjuster
Human review required: Yes
Reason codes:
- Injury reported
- Third party involved
- High estimated damage
```

### 22.4 Human Override Modal

Fields:

```text
Decision:
  Accept AI recommendation
  Override severity
  Override fraud risk
  Escalate to SIU
  Request documents
  Approve claim
  Reject claim

Override reason:
  required if overriding AI
```

---

## 23. Example End-to-End Demo Scenario

Use this as the main demo.

### Scenario

A motor policyholder reports a rear-end accident in Bielefeld.

Input:

```text
Policy: Active motor policy
Loss date: 2026-06-20
FNOL date: 2026-06-26
Claim type: Motor collision
Estimated damage: 8,400 EUR
Third party involved: yes
Injury reported: yes
Police report: missing
Prior claims: 2
```

### Expected System Behavior

1. FNOL is submitted.
2. Policy is found.
3. Policy was active on loss date.
4. Collision coverage is available.
5. Claim is created.
6. AI triage predicts:
   - Severity: HIGH
   - Fraud risk: MEDIUM
   - Litigation risk: MEDIUM
7. Reason codes:
   - Injury reported.
   - Third party involved.
   - High estimated damage.
   - Missing police report.
   - Late FNOL.
8. Claim is routed to Senior Motor Adjuster.
9. Document intelligence detects police report missing.
10. RAG assistant explains coverage and missing documents.
11. Adjuster requests police report.
12. Audit log stores all actions.

### Demo Talking Points

Say:

> This project simulates how an insurer can connect policy validation, claim intake,
> AI triage, and document intelligence around a Guidewire-style claims workflow.
> AI does not approve or reject the claim. It supports adjusters with risk signals,
> summaries, missing document detection, and evidence-grounded recommendations.

---

## 24. Resume Positioning

After completing MVP, use this project entry:

```text
InsureFlow AI — Cloud-Native Claims & Policy Intelligence Platform
Java, Spring Boot, Python, FastAPI, PostgreSQL, pgvector, Vue.js, Docker, XGBoost, LLM/RAG

- Built an enterprise-style P&C insurance platform inspired by Guidewire ClaimCenter and PolicyCenter workflows, supporting FNOL intake, policy lookup, coverage validation, claim lifecycle management, and adjuster assignment.
- Developed AI triage services to predict claim severity, fraud risk, and litigation likelihood with explainable reason codes and human-in-the-loop review.
- Implemented LLM-based document intelligence for claim description extraction, repair invoice parsing, missing-document detection, and adjuster-ready claim summaries.
- Built a RAG-based adjuster assistant using policy documents, claim notes, and insurance guidelines with source-grounded answers and audit logging.
- Designed Guidewire-style REST integration APIs, event-driven claim status updates, PostgreSQL data modeling, Dockerized deployment, automated tests, and OpenAPI documentation.
```

---

## 25. GitHub Portfolio Requirements

The GitHub repository must look professional.

### 25.1 Required Badges

Add badges for:

- Build status.
- Backend tests.
- Python tests.
- Docker.
- License.
- Java version.
- Python version.

### 25.2 Required Visuals

Add:

- Architecture diagram.
- ER diagram.
- Claim workflow diagram.
- AI triage flow.
- RAG pipeline diagram.
- Screenshots of adjuster dashboard.
- Demo GIF or video.

### 25.3 Required README Sections

- Problem.
- Solution.
- Features.
- Architecture.
- Tech stack.
- Dataset strategy.
- AI/ML design.
- Responsible AI.
- Local setup.
- API docs.
- Demo scenario.
- Roadmap.
- Limitations.
- References.

---

## 26. Risks and Mitigations

### Risk 1: Project Becomes Too Big

Mitigation:

- Build phase by phase.
- First deliver a working MVP.
- Avoid overengineering early.
- Keep frontend simple until backend/AI works.

### Risk 2: No Real Guidewire Access

Mitigation:

- Clearly say “Guidewire-inspired.”
- Use public Guidewire API/documentation concepts.
- Build REST/OpenAPI integration patterns.
- Focus on domain workflows.

### Risk 3: Synthetic Data Seems Fake

Mitigation:

- Use public fraud dataset for ML proof.
- Generate relational synthetic data with realistic rules.
- Document data generation assumptions.
- Add distributions and charts.

### Risk 4: LLM Hallucination

Mitigation:

- Use RAG.
- Require sources.
- Add “not enough evidence” behavior.
- Store prompt and response.
- Use schema validation.

### Risk 5: AI Looks Decorative

Mitigation:

- Integrate AI into claim workflow.
- Use ML scores for queue assignment.
- Use LLM for actual document extraction and summaries.
- Add human review.

### Risk 6: Too Much Infrastructure

Mitigation:

- Use Docker Compose first.
- Use RabbitMQ before Kafka.
- Use pgvector before separate vector DB.
- Deploy only after local MVP works.

---

## 27. Learning Plan While Building

### 27.1 Insurance Domain Topics to Learn

Learn as needed:

1. P&C insurance basics.
2. Policy lifecycle.
3. Claim lifecycle.
4. FNOL.
5. Coverage and exclusions.
6. Deductibles and limits.
7. Claims adjuster workflow.
8. Fraud indicators.
9. Litigation risk.
10. Subrogation.
11. Reserving basics.
12. Loss ratio basics.

### 27.2 Guidewire Topics to Learn

Learn enough to speak clearly:

1. ClaimCenter.
2. PolicyCenter.
3. BillingCenter.
4. InsuranceSuite.
5. Guidewire Cloud.
6. Cloud APIs.
7. Gosu basics.
8. Integration patterns.
9. Data model concepts.
10. Partner ecosystem.

### 27.3 AI/ML Topics to Learn

1. Imbalanced classification.
2. Fraud detection.
3. Severity prediction.
4. Feature engineering.
5. Model explainability.
6. SHAP.
7. ML model serving.
8. Model cards.
9. RAG.
10. Prompt versioning.
11. LLM evaluation.
12. Responsible AI.

---

## 28. Local Development Commands

These are target commands. Implement scripts accordingly.

### Start Infrastructure

```bash
docker compose up -d postgres rabbitmq
```

### Start Backend

```bash
cd backend
mvn clean install
mvn spring-boot:run -pl claims-service
```

### Start AI Service

```bash
cd ai-services
uvicorn triage_service.app.main:app --reload --port 8001
```

### Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### Generate Synthetic Data

```bash
cd synthetic-data-generator
python -m generator.generate --customers 5000 --policies 6500 --claims 2000
```

### Load Sample Data

```bash
./scripts/load-sample-data.sh
```

### Run Tests

```bash
./scripts/run-tests.sh
```

---

## 29. Codex Implementation Instructions

When using Codex or an AI coding agent:

1. Always read this blueprint first.
2. Do not build random features outside the roadmap.
3. Implement one phase at a time.
4. Keep commits small and meaningful.
5. Add tests with each feature.
6. Update documentation when code changes.
7. Do not hardcode API keys.
8. Do not use real personal data.
9. Maintain clear package structure.
10. Prefer working vertical slices over incomplete abstractions.

### Recommended First Codex Prompt

```text
Read PROJECT_BLUEPRINT.md completely. Start Phase 0 and Phase 1 only.
Create the repository structure, Docker Compose for PostgreSQL/RabbitMQ,
a Spring Boot backend skeleton, Flyway migrations for Customer, Policy,
Coverage, Claim, ClaimDocument, ClaimEvent, Adjuster, AITriageResult, and
AuditLog, and basic OpenAPI setup. Add tests for schema bootstrapping.
Do not implement AI yet. Keep the design aligned with the blueprint.
```

### Recommended Second Codex Prompt

```text
Continue from the current repository. Implement Phase 2: synthetic data generator.
Create Python scripts to generate customers, policies, coverages, claims, claim
documents, claim notes, claim events, adjusters, and labels for severity/fraud/
litigation. Ensure referential integrity and realistic distributions. Add README
and tests for generated data consistency.
```

### Recommended Third Codex Prompt

```text
Implement Phase 3 and Phase 4. Add policy CRUD, coverage validation, FNOL claim
submission, claim lifecycle states, claim timeline, and integration tests using
Testcontainers. Ensure Swagger documents all endpoints and errors use the shared
error response format.
```

### Recommended Fourth Codex Prompt

```text
Implement Phase 5. Create FastAPI AI triage service with rule-based severity,
fraud, and litigation scoring. Add Pydantic schemas, reason codes, tests, and
integrate Claims Service with the triage endpoint. Store triage output and audit
details in PostgreSQL.
```

### Recommended Fifth Codex Prompt

```text
Implement Phase 6. Add ML training pipeline for fraud and severity models using
the public fraud dataset and synthetic data. Add preprocessing, train/evaluate
baseline and tree-based models, save model artifacts, add model cards, and serve
the model through the FastAPI triage service.
```

---

## 30. Final Success Criteria

The project is successful when:

1. A user can submit a claim.
2. The system validates policy coverage.
3. The AI service scores severity and fraud risk.
4. The LLM service extracts and summarizes documents.
5. The adjuster dashboard shows claim intelligence.
6. A human can review and override AI recommendations.
7. Audit logs capture AI and human decisions.
8. The system runs locally with Docker.
9. The repository has professional documentation.
10. The project can be explained in a 5-minute recruiter demo.
11. The project can be discussed technically in a 45-minute interview.
12. The project clearly connects Java, insurance domain, cloud, data, AI/ML, LLMs, and Guidewire-inspired workflows.

---

## 31. References and Source Anchors

Use these references in the README and documentation.

1. Guidewire Cloud APIs  
   https://www.guidewire.com/developers/apis/cloud-apis  
   Key idea: InsuranceSuite Cloud API is a set of RESTful system APIs used by applications to request data from or initiate actions in InsuranceSuite.

2. Guidewire ClaimCenter Cloud API Documentation  
   https://docs.guidewire.com/cloud/cc/202503/apiref/  
   Key idea: APIs provide content for the REST API framework and are built using Swagger specifications.

3. Guidewire PolicyCenter Cloud API Documentation  
   https://docs.guidewire.com/cloud/pc/202503/apiref/  
   Key idea: PolicyCenter APIs follow the same REST/Swagger-oriented Cloud API approach.

4. Guidewire Claims Solutions  
   https://www.guidewire.com/products/solutions/claims-solutions  
   Key idea: Claims analytics can analyze claim attributes at FNOL, identify severe claims early, identify subrogation opportunities, and analyze litigation likelihood.

5. Guidewire Insurance AI  
   https://www.guidewire.com/products/technology/insurance-ai-from-guidewire  
   Key idea: AI is being applied to quoting, underwriting, claims, and service on insurance platforms.

6. Vehicle Insurance Fraud Detection Dataset  
   https://www.kaggle.com/datasets/khusheekapoor/vehicle-insurance-fraud-detection  
   Key idea: Public automobile insurance fraud dataset with significant class imbalance.

7. Auto Insurance Claims Data  
   https://www.kaggle.com/datasets/buntyshah/auto-insurance-claims-data  
   Key idea: Public auto insurance claims dataset commonly used for fraud detection practice.

8. RISC / RISCBAC Synthetic Insurance Contracts  
   https://arxiv.org/abs/2304.04212  
   Key idea: Synthetic bilingual automobile insurance contracts for NLP tasks.

9. SynthETIC Claim Simulator  
   https://arxiv.org/abs/2008.05693  
   Key idea: Open-source individual non-life insurance claim simulator with feature control.

10. SynthETIC GitHub Repository  
    https://github.com/agi-lab/SynthETIC  
    Key idea: Open-source simulator that generates non-life insurance claim features.

---

## 32. Final Project Positioning Statement

Use this statement in interviews:

> InsureFlow AI is a cloud-native insurance technology project inspired by Guidewire-style policy and claims workflows. It combines Java/Spring Boot core services, PostgreSQL insurance data modeling, ML-based severity and fraud risk scoring, LLM-based document intelligence, RAG-based adjuster assistance, human-in-the-loop review, audit logging, and Guidewire-style REST integration APIs. The goal is to demonstrate how AI can responsibly support claims operations without replacing human decision-makers.

---

## 33. Immediate Next Step

Start with Phase 0 and Phase 1.

Do not start with the ML model first.

The correct order is:

```text
1. Repository structure
2. Database and domain model
3. Synthetic data generator
4. Policy and claim workflow
5. Rule-based AI triage
6. ML model training
7. LLM document intelligence
8. RAG assistant
9. Frontend dashboard
10. Cloud deployment and polish
```

This order ensures that AI is integrated into a real insurance workflow instead of becoming an isolated notebook.
