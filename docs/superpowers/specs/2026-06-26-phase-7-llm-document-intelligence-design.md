# Phase 7 LLM Document Intelligence Design

## Context

Phase 7 adds the first LLM-style capability to InsureFlow AI: structured extraction and adjuster-ready summarization from claim text and claim documents. Phase 5 and Phase 6 already provide deterministic claim triage. Phase 7 must complement those services without making final claim decisions, fraud accusations, legal advice, or medical advice.

The service will be built as a separate FastAPI application under `ai-services/document-intelligence-service`, following the existing triage service pattern. It will run offline by default with a deterministic local provider so tests and demos do not require API keys or network access. The architecture will include a provider boundary so a hosted LLM client can be added later without changing the API contract.

## Recommended Approach

I considered three approaches:

1. **Hosted LLM first:** call OpenAI or Azure OpenAI directly from the new service.
   This best matches the long-term product vision, but it makes local tests dependent on secrets, latency, cost, and network access.

2. **Deterministic local provider first:** implement prompt templates, schema validation, retry behavior, audit records, and realistic extraction/summarization rules without an external LLM call.
   This is the recommended Phase 7 approach. It keeps the project runnable for recruiters and future agents while preserving the right architecture for real LLM integration.

3. **Backend-only document intelligence:** add document extraction directly inside the Spring Boot API.
   This would reduce service count, but it mixes Java claim workflow with Python LLM orchestration and breaks the AI-service pattern already established by triage.

Phase 7 will use option 2.

## Scope

Phase 7 includes:

- A new FastAPI document intelligence service.
- Health endpoint.
- Prompt template registry with prompt names, versions, model labels, temperature, and schema names.
- Claim description extraction.
- Repair invoice extraction.
- Claim file summary generation.
- Missing document detection.
- Pydantic response schemas and validation.
- One retry when the provider returns invalid JSON for extraction.
- In-memory prompt audit records containing prompt version, rendered prompt, raw response, parsed output, and validation status.
- Tests using synthetic insurance text.
- Documentation for API contracts, prompt behavior, and local usage.

Phase 7 does not include:

- RAG ingestion, embeddings, pgvector, or source-grounded question answering. That is Phase 8.
- Real OpenAI/Azure OpenAI calls. The provider boundary will make this easy later.
- Backend persistence of document intelligence outputs. This phase establishes the AI service contract first.
- Frontend screens.
- Production-grade audit storage.

## Service Boundaries

The new service owns LLM-style document behavior:

- It receives claim or document text.
- It renders the correct prompt template.
- It invokes the configured provider.
- It validates and normalizes output with Pydantic.
- It stores an audit record.
- It returns structured, explainable output to callers.

The Spring Boot backend remains the system of record for claims, policies, documents, and future persisted AI outputs. Integration from backend to this service can be added after the AI contract is stable.

## API Contract

### `GET /health`

Returns service liveness:

```json
{
  "status": "ok",
  "service": "document-intelligence-service"
}
```

### `GET /ai/v1/documents/health`

Returns the same payload as `/health`, matching the blueprint endpoint style.

### `POST /ai/v1/documents/extract`

Request:

```json
{
  "claimId": "CLM-ID-001",
  "claimNumber": "CLM-20260626-000001",
  "documentId": "DOC-001",
  "documentType": "CLAIM_DESCRIPTION",
  "text": "I was driving near Bielefeld when another car hit my rear bumper...",
  "knownDocuments": ["DAMAGE_PHOTOS"]
}
```

Supported `documentType` values for Phase 7:

- `CLAIM_DESCRIPTION`
- `REPAIR_INVOICE`
- `POLICE_REPORT`
- `MEDICAL_NOTE`
- `POLICY_DOCUMENT`
- `CUSTOMER_EMAIL`
- `ADJUSTER_NOTE`

For `CLAIM_DESCRIPTION`, the response includes normalized claim facts:

```json
{
  "claimId": "CLM-ID-001",
  "claimNumber": "CLM-20260626-000001",
  "documentId": "DOC-001",
  "documentType": "CLAIM_DESCRIPTION",
  "promptName": "claim_description_extraction",
  "promptVersion": "v1",
  "modelName": "deterministic-document-intelligence",
  "auditId": "AUD-...",
  "extractedFields": {
    "claimType": "MOTOR_COLLISION",
    "damageType": "REAR_BUMPER",
    "thirdPartyInvolved": true,
    "policeReportAvailable": false,
    "possibleHitAndRun": true,
    "estimatedDamageAmount": 4500,
    "injuryReported": false,
    "requiredDocuments": ["POLICE_REPORT", "DAMAGE_PHOTOS", "REPAIR_ESTIMATE"]
  },
  "validationWarnings": []
}
```

For `REPAIR_INVOICE`, `extractedFields` contains:

```json
{
  "invoiceNumber": "INV-2026-10042",
  "repairShop": "Example Auto Repair GmbH",
  "laborCost": 1200,
  "partsCost": 2800,
  "taxAmount": 760,
  "totalAmount": 4760,
  "currency": "EUR"
}
```

Unsupported document types return a structured extraction response with available metadata and a validation warning rather than a server error. This keeps document intake resilient while making unsupported extraction explicit.

### `POST /ai/v1/documents/missing-check`

Request:

```json
{
  "claimId": "CLM-ID-001",
  "claimNumber": "CLM-20260626-000001",
  "claimType": "MOTOR_COLLISION",
  "injuryReported": false,
  "thirdPartyInvolved": true,
  "policeReportAvailable": false,
  "knownDocuments": ["DAMAGE_PHOTOS"]
}
```

Response:

```json
{
  "claimId": "CLM-ID-001",
  "claimNumber": "CLM-20260626-000001",
  "promptName": "missing_documents",
  "promptVersion": "v1",
  "auditId": "AUD-...",
  "missingDocuments": ["POLICE_REPORT", "REPAIR_ESTIMATE"],
  "explanation": "Police report and repair estimate should be requested before adjuster review.",
  "requiresHumanReview": true
}
```

### `POST /ai/v1/documents/summarize`

Request:

```json
{
  "claimId": "CLM-ID-001",
  "claimNumber": "CLM-20260626-000001",
  "claimType": "MOTOR_COLLISION",
  "policyStatus": "ACTIVE",
  "coverageStatus": "COVERED",
  "incidentDetails": "Rear bumper collision near Bielefeld.",
  "documentsReceived": ["DAMAGE_PHOTOS", "REPAIR_INVOICE"],
  "missingDocuments": ["POLICE_REPORT"],
  "triage": {
    "severity": "HIGH",
    "fraud": "MEDIUM",
    "litigation": "LOW"
  },
  "keyInconsistencies": ["Invoice amount exceeds initial estimate."],
  "recommendedNextAction": "Request police report and assign to senior motor adjuster."
}
```

Response:

```json
{
  "claimId": "CLM-ID-001",
  "claimNumber": "CLM-20260626-000001",
  "promptName": "claim_summary",
  "promptVersion": "v1",
  "auditId": "AUD-...",
  "sections": {
    "claimOverview": "...",
    "policyAndCoverageStatus": "...",
    "incidentDetails": "...",
    "documentsReceived": "...",
    "missingDocuments": "...",
    "aiRiskScores": "...",
    "keyInconsistencies": "...",
    "recommendedNextAction": "...",
    "humanReviewWarning": "This is decision support only. A licensed adjuster must review the claim."
  },
  "summaryText": "..."
}
```

## Prompt Registry

Prompt templates will be defined in code for Phase 7:

| Prompt Name | Version | Purpose | Schema |
| --- | --- | --- | --- |
| `claim_description_extraction` | `v1` | Extract claim facts from FNOL/loss text. | `ClaimDescriptionExtraction` |
| `repair_invoice_extraction` | `v1` | Extract invoice fields from repair invoice text. | `RepairInvoiceExtraction` |
| `missing_documents` | `v1` | Explain documents still needed for review. | `MissingDocumentsResponse` |
| `claim_summary` | `v1` | Produce adjuster-ready claim summary sections. | `ClaimSummaryResponse` |

The registry will include prompt template text, model name, temperature, and output schema label. Prompt names and versions will be returned in API responses and stored in audit records.

## Provider And Retry Behavior

The service will define a provider protocol with one method:

```python
generate_json(prompt: RenderedPrompt) -> str
```

The default provider will be deterministic and local. It will return JSON strings so the service exercises the same parsing and validation path used by a real LLM client.

Extraction calls will retry once when JSON parsing or schema validation fails. The retry prompt will include an instruction to return valid JSON only. If both attempts fail, the service will return HTTP 422 with a concise validation error and store an audit record showing failure.

## Audit

Phase 7 audit storage is in-memory and process-local. Each audit record includes:

- `auditId`
- `claimId`
- `claimNumber`
- `documentId`
- `documentType`
- `promptName`
- `promptVersion`
- `modelName`
- `renderedPrompt`
- `rawResponse`
- `parsedOutput`
- `validationStatus`
- `errorMessage`
- `createdAt`

This is enough for local demos and tests. A later backend phase can persist these records in PostgreSQL.

## Safety And Responsible AI

Responses must:

- State that summaries and missing-document recommendations are decision support only.
- Avoid final approval or rejection language.
- Avoid fraud accusations.
- Avoid legal or medical advice.
- Prefer human review when evidence is missing, contradictory, or high risk.
- Never expose secrets or API keys.

## Testing Strategy

Tests will cover:

- Health endpoints.
- Claim description extraction from synthetic loss text.
- Repair invoice extraction from synthetic invoice text.
- Missing police report detection.
- Summary response includes all required sections and human review warning.
- Invalid JSON retry succeeds when the provider fails once.
- Invalid JSON failure returns HTTP 422 after retry.
- Prompt audit records include raw response, prompt version, and parsed output.

The root `scripts/run-tests.sh` will be updated to include the new service test suite.

## Documentation Updates

Phase 7 will add:

- `docs/api/document-intelligence.md`
- `ai-services/document-intelligence-service/README.md`
- Links from the root README, docs index, and AI services README.
- Project memory entries for branch creation, design, implementation, verification, and PR.

## Done Criteria

Phase 7 is done when:

- Documentation and implementation plan are committed.
- The new FastAPI service has extraction, summary, missing-check, prompt registry, retry, and audit behavior.
- Service tests pass.
- The full repository test script passes.
- Project memory is updated.
- A pull request is opened from `llm-document-intelligence` into `main`.
