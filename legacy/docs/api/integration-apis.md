# Phase 10 Integration APIs

Phase 10 adds Guidewire-inspired system integration APIs under `/integration/v1`.

These endpoints are not official Guidewire connectors. They demonstrate how a core insurance platform can expose adapter-style APIs for policy sync, claim creation, claim status updates, reserve updates, claim lookup, and webhook acknowledgement.

## Design

The integration API is a facade over existing InsureFlow AI domain services:

- policy sync delegates to customer, policy, coverage, and activation workflows;
- claim create delegates to the FNOL workflow and coverage validation;
- claim status update delegates to the claim workflow service;
- reserve update persists a claim reserve and writes a claim timeline event;
- webhook simulation records an integration event and returns an acknowledgement.

Phase 10 stores lightweight operational integration events in `integration_events`. Full security, JWT roles, correlation IDs, and governance audit belong to Phase 11.

## Base URL

```text
http://localhost:8080/integration/v1
```

## Policy Sync

`POST /integration/v1/policies/sync`

```json
{
  "sourceSystem": "PolicyCenter",
  "externalReference": "PC-POL-1001",
  "customer": {
    "customerNumber": "CUST-INT-1001",
    "firstName": "Avery",
    "lastName": "Stone",
    "email": "avery.stone@example.test",
    "country": "US"
  },
  "policy": {
    "policyNumber": "POL-INT-1001",
    "policyType": "PERSONAL_AUTO",
    "effectiveDate": "2026-01-01",
    "expirationDate": "2027-01-01",
    "premiumAmount": 1425.00,
    "currency": "USD",
    "activate": true
  },
  "coverages": [
    {
      "coverageCode": "COLLISION",
      "coverageName": "Collision Coverage",
      "coverageType": "COLLISION",
      "limitAmount": 30000.00,
      "deductibleAmount": 500.00,
      "effectiveDate": "2026-01-01",
      "expirationDate": "2027-01-01",
      "exclusions": "[]"
    }
  ]
}
```

Response `201 Created`:

```json
{
  "policyNumber": "POL-INT-1001",
  "customerNumber": "CUST-INT-1001",
  "status": "ACTIVE",
  "coverageCount": 1,
  "integrationEventId": "..."
}
```

## Create Claim

`POST /integration/v1/claims`

```json
{
  "sourceSystem": "ClaimCenter",
  "externalReference": "CC-CLAIM-1001",
  "claim": {
    "policyNumber": "POL-INT-1001",
    "claimType": "AUTO_COLLISION",
    "lossDate": "2026-06-24",
    "reportedAt": "2026-06-25T10:15:30Z",
    "lossLocation": "Columbus, OH",
    "description": "Rear-end collision reported through integration API.",
    "estimatedLossAmount": 9200.00
  }
}
```

Response `201 Created` includes the generated `claimNumber`, current `status`, claim facts, linked policy summary, and `integrationEventId`.

## Claim Lookup

`GET /integration/v1/claims/{claimNumber}`

Returns the current claim status and policy reference for integration consumers.

## Claim Status Update

`POST /integration/v1/claims/{claimNumber}/status`

```json
{
  "sourceSystem": "ClaimCenter",
  "externalReference": "CC-STATUS-1001",
  "targetStatus": "UNDER_REVIEW",
  "reason": "Integration queue assignment"
}
```

The endpoint uses the same transition rules as `/api/v1/claims/{claimNumber}/status`. Invalid transitions return HTTP 422.

## Reserve Update

`POST /integration/v1/claims/{claimNumber}/reserves`

```json
{
  "sourceSystem": "ClaimCenter",
  "externalReference": "CC-RES-1001",
  "coverageCode": "COLLISION",
  "reserveAmount": 8500.00,
  "currency": "USD",
  "reason": "Initial collision reserve"
}
```

Response `201 Created`:

```json
{
  "claimNumber": "CLM-20260626-0001",
  "coverageCode": "COLLISION",
  "reserveAmount": 8500.00,
  "currency": "USD",
  "reason": "Initial collision reserve",
  "reserveId": "...",
  "integrationEventId": "..."
}
```

Reserve updates also write a claim timeline event with type `RESERVE_UPDATED`.

## Claim-Triaged Webhook Simulation

`POST /integration/v1/webhooks/claim-triaged`

```json
{
  "sourceSystem": "TriageService",
  "externalReference": "TRIAGE-1001",
  "claimNumber": "CLM-20260626-0001",
  "severityLabel": "HIGH",
  "fraudRiskLabel": "MEDIUM",
  "recommendedQueue": "SENIOR_ADJUSTER",
  "humanReviewRequired": true
}
```

Response `202 Accepted`:

```json
{
  "accepted": true,
  "claimNumber": "CLM-20260626-0001",
  "integrationEventId": "..."
}
```

## Error Handling

- Bad payloads return HTTP 400 with the existing `ApiErrorResponse` shape.
- Unknown claims and policies return HTTP 404.
- Invalid claim status transitions return HTTP 422.

## Local Verification

```bash
cd backend
mvn -pl api test -Dtest=IntegrationApiIntegrationTest
```

The replayable HTTP collection is available at [`collections/phase-10-integration-apis.http`](collections/phase-10-integration-apis.http).
