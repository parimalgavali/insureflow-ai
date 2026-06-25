# AI Triage API

Phase 5 adds a rule-based AI triage service and connects it to the claims workflow. The AI service is decision support only: outputs help route claims for human review and should not be used as automated claim approval, denial, fraud accusation, legal advice, or medical advice.

## Components

- Python FastAPI service: `ai-services/triage-service`
- Java backend client and workflow integration: `backend/api/src/main/java/com/insureflow/api/ai/triage`
- Persistent triage results: `ai_triage_results`
- Timeline event emitted after successful triage: `TRIAGE_COMPLETED`

## Python Service

Run tests:

```bash
cd ai-services/triage-service
python3 -m pip install -e ".[test]"
python3 -m pytest
```

Run locally:

```bash
cd ai-services/triage-service
python3 -m uvicorn triage_service.app:app --reload --port 8001
```

Health check:

```http
GET /health
```

Scoring endpoint:

```http
POST /ai/v1/triage/score
```

Example request:

```json
{
  "claimId": "claim-123",
  "claimNumber": "CLM-2026-0001",
  "policyFeatures": {
    "policyType": "PERSONAL_AUTO",
    "policyAgeDays": 175,
    "coverageLimitAmount": 25000.00,
    "deductibleAmount": 500.00,
    "coverageValid": true,
    "coverageReasons": []
  },
  "claimFeatures": {
    "claimType": "AUTO_COLLISION",
    "estimatedLossAmount": 30000.00,
    "injuryReported": true,
    "thirdPartyInvolved": true,
    "policeReportAvailable": false,
    "lossReportDelayDays": 1,
    "priorClaimsCount": 0
  },
  "textFeatures": {
    "lossDescription": "Rear-end collision with injury reported by the other driver."
  }
}
```

Example response:

```json
{
  "claimId": "claim-123",
  "claimNumber": "CLM-2026-0001",
  "modelName": "rule-based-triage",
  "modelVersion": "rules-v1",
  "severity": {
    "label": "HIGH",
    "score": 0.82,
    "reasonCodes": ["INJURY_REPORTED", "HIGH_ESTIMATED_DAMAGE"]
  },
  "fraud": {
    "label": "LOW",
    "score": 0.18,
    "reasonCodes": []
  },
  "litigation": {
    "label": "MEDIUM",
    "score": 0.46,
    "reasonCodes": ["THIRD_PARTY_INVOLVED"]
  },
  "recommendedQueue": "COMPLEX_CLAIMS",
  "humanReviewRequired": true,
  "explanation": "Injury and high estimated damage require review."
}
```

## Backend Workflow Endpoints

Run triage for an existing claim:

```http
POST /api/v1/claims/{claimNumber}/triage
```

Fetch the latest persisted triage result:

```http
GET /api/v1/claims/{claimNumber}/triage
```

Example backend response:

```json
{
  "claimNumber": "CLM-2026-0001",
  "modelName": "rule-based-triage",
  "modelVersion": "rules-v1",
  "severityScore": 0.82,
  "severityLabel": "HIGH",
  "fraudRiskScore": 0.18,
  "fraudRiskLabel": "LOW",
  "litigationRiskScore": 0.46,
  "litigationRiskLabel": "MEDIUM",
  "recommendedQueue": "COMPLEX_CLAIMS",
  "reasonCodes": ["INJURY_REPORTED", "HIGH_ESTIMATED_DAMAGE", "THIRD_PARTY_INVOLVED"],
  "humanReviewRequired": true,
  "explanation": "Injury and high estimated damage require review.",
  "createdAt": "2026-06-25T10:30:00Z"
}
```

If the AI service is unavailable, the backend returns:

```json
{
  "status": 503,
  "error": "Service Unavailable",
  "message": "AI triage service is unavailable"
}
```

## Backend Configuration

The backend calls the Python service using:

```yaml
insureflow:
  ai:
    triage:
      base-url: http://localhost:8001
```

Override this value per environment when the Python service runs elsewhere.

## Verification

Targeted backend checks:

```bash
cd backend
mvn -pl api test -Dtest=ClaimTriageIntegrationTest,ClaimTriageFailureIntegrationTest,RestTriageClientTest,AiTriageResultRepositoryTest
```

Full project check:

```bash
./scripts/run-tests.sh
```
