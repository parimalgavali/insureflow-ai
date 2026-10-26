# Document Intelligence API

Phase 7 adds a FastAPI document intelligence service under `ai-services/document-intelligence-service`. It extracts structured fields from claim text and documents, identifies missing claim documents, and generates adjuster-ready claim summaries.

The service uses a deterministic local provider by default. This intentionally behaves like an LLM client returning JSON strings, but it does not call an external model. The design keeps local development, tests, and portfolio demos runnable without API keys.

Phase 18 adds a Spring Boot product facade for frontend document workspace reads:

```http
GET /api/v1/claims/{claimNumber}/document-workspace
```

The Vue app calls this backend facade, not the Python service directly. The facade builds an adjuster-ready workspace from persisted claim, coverage, triage, and document metadata. The standalone Python service remains the lower-level document-intelligence service for extraction, missing-document checks, and future orchestration.

## Boundaries

The service is decision support only. It must not approve or reject claims, make fraud accusations, provide legal advice, provide medical advice, or replace human adjuster review.

Phase 7 does not implement RAG. Source-grounded adjuster Q&A, embeddings, and retrieval are reserved for Phase 8.

## Local Run

```bash
cd ai-services/document-intelligence-service
python3 -m pip install -e ".[test]"
python3 -m pytest
python3 -m uvicorn document_intelligence.app:app --reload --port 8002
```

## Health

```http
GET /health
GET /ai/v1/documents/health
```

Response:

```json
{
  "status": "ok",
  "service": "document-intelligence-service"
}
```

## Extract Document Fields

```http
POST /ai/v1/documents/extract
```

Request:

```json
{
  "claimId": "CLM-ID-001",
  "claimNumber": "CLM-20260626-000001",
  "documentId": "DOC-001",
  "documentType": "CLAIM_DESCRIPTION",
  "text": "I was driving near Bielefeld when another car hit my rear bumper. The driver left the scene. I have photos but no police report yet. Damage is around 4500 EUR.",
  "knownDocuments": ["DAMAGE_PHOTOS"]
}
```

Response:

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

Supported Phase 7 document types:

- `CLAIM_DESCRIPTION`
- `REPAIR_INVOICE`
- `POLICE_REPORT`
- `MEDICAL_NOTE`
- `POLICY_DOCUMENT`
- `CUSTOMER_EMAIL`
- `ADJUSTER_NOTE`

`CLAIM_DESCRIPTION` and `REPAIR_INVOICE` have structured extraction schemas in Phase 7. Other document types are accepted in the enum so the API can evolve without changing the intake contract.

## Missing Document Check

```http
POST /ai/v1/documents/missing-check
```

## Spring Boot Document Workspace Facade

```http
GET /api/v1/claims/CLM-20260626-000418/document-workspace
```

Response:

```json
{
  "claimNumber": "CLM-20260626-000418",
  "receivedDocuments": ["DAMAGE_PHOTOS", "REPAIR_INVOICE"],
  "missingDocuments": ["POLICE_REPORT"],
  "extractionHighlights": [
    "Received 2 document type(s) for live backend review.",
    "Estimated loss amount is 8400 EUR.",
    "Missing required document(s): POLICE_REPORT."
  ],
  "summarySections": [
    {
      "title": "Claim overview",
      "body": "Rear bumper collision near Bielefeld."
    },
    {
      "title": "Recommended next action",
      "body": "Request missing documents and keep the claim in human review."
    }
  ]
}
```

The facade is deterministic in Phase 18. It does not approve or reject claims and should be treated as decision support.

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
  "explanation": "Police report should be requested because a third party is involved. Repair estimate should be requested to validate the claimed damage amount.",
  "requiresHumanReview": true
}
```

## Claim Summary

```http
POST /ai/v1/documents/summarize
```

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
    "claimOverview": "Claim CLM-20260626-000001 is a MOTOR_COLLISION claim.",
    "policyAndCoverageStatus": "The policy status is ACTIVE and the current coverage status is COVERED.",
    "incidentDetails": "Rear bumper collision near Bielefeld.",
    "documentsReceived": "DAMAGE_PHOTOS, REPAIR_INVOICE",
    "missingDocuments": "POLICE_REPORT",
    "aiRiskScores": "Severity is HIGH, fraud risk is MEDIUM, and litigation risk is LOW.",
    "keyInconsistencies": "Invoice amount exceeds initial estimate.",
    "recommendedNextAction": "Request police report and assign to senior motor adjuster.",
    "humanReviewWarning": "This summary is decision support only. A qualified adjuster must review the claim before any decision."
  },
  "summaryText": "..."
}
```

## Prompt Versioning

Phase 7 prompt names:

| Prompt | Version | Purpose |
| --- | --- | --- |
| `claim_description_extraction` | `v1` | Extract FNOL/loss facts. |
| `repair_invoice_extraction` | `v1` | Extract invoice fields. |
| `missing_documents` | `v1` | Identify missing claim documents. |
| `claim_summary` | `v1` | Generate adjuster summary sections. |

Each response returns `promptName`, `promptVersion`, and `auditId`.

## Validation And Retry

The provider returns raw JSON strings. The service parses and validates those strings with Pydantic schemas. If JSON parsing or schema validation fails, the service retries once with a stricter JSON-only instruction. If the retry fails, the endpoint returns HTTP 422 and records an invalid audit entry.

## Audit

Phase 7 uses an in-memory audit store. Each record contains:

- prompt name and version
- rendered prompt
- raw provider response
- parsed output when valid
- validation status
- error message when invalid
- claim and document identifiers

This audit store is local and process-scoped. A later backend phase can persist document intelligence audit records in PostgreSQL.
