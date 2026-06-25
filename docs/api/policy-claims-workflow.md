# Policy Claims Workflow API

This document describes the Phase 3/4 backend workflow: customer, policy, coverage validation, FNOL claim intake, timeline events, notes, and document metadata.

## Run Locally

```bash
docker compose up -d postgres rabbitmq
cd backend
mvn test
```

To inspect the API manually, start the Spring Boot app and open Swagger:

```bash
cd backend
mvn -pl api spring-boot:run
```

Swagger UI: `http://localhost:8080/swagger-ui.html`

## Demo Flow

Base URL: `http://localhost:8080/api/v1`

1. Create a customer with `POST /customers`.
2. Create a draft policy with `POST /policies`.
3. Add coverage with `POST /policies/{policyNumber}/coverages`.
4. Activate the policy with `POST /policies/{policyNumber}/activate`.
5. Validate coverage with `POST /policies/{policyNumber}/coverage-check`.
6. Submit FNOL with `POST /claims/fnol`.
7. Read the claim with `GET /claims/{claimNumber}`.
8. Read timeline events with `GET /claims/{claimNumber}/events`.
9. Add a note with `POST /claims/{claimNumber}/notes`.
10. Add document metadata with `POST /claims/{claimNumber}/documents`.
11. Change claim status with `POST /claims/{claimNumber}/status`.

## Key Business Rules

- Policies start as `DRAFT`.
- Only `DRAFT` policies can be activated.
- Only `ACTIVE` policies can be cancelled, expired, or renewed.
- Coverage validation checks policy active status, loss date, claim type mapping, coverage limit, deductible, and exclusions.
- FNOL creates a claim even when coverage has issues, but the response and timeline record those issues.
- Claim status transitions are constrained by the workflow table from the Phase 3/4 plan.

## Claim Type To Coverage Mapping

| Claim Type | Required Coverage Type |
| --- | --- |
| `AUTO_COLLISION` | `COLLISION` |
| `AUTO_COMPREHENSIVE` | `COMPREHENSIVE` |
| `BODILY_INJURY` | `BODILY_INJURY` |
| `PROPERTY_DAMAGE` | `PROPERTY_DAMAGE` |
| `HOME_WATER_DAMAGE` | `WATER_DAMAGE` |
| `HOME_FIRE` | `FIRE` |
| `THEFT` | `THEFT` |

## Example Requests

Create customer:

```json
{
  "customerNumber": "CUST-DEMO-1001",
  "firstName": "Maya",
  "lastName": "Chen",
  "email": "maya.chen@example.test",
  "country": "US"
}
```

Create policy:

```json
{
  "customerNumber": "CUST-DEMO-1001",
  "policyNumber": "POL-DEMO-1001",
  "policyType": "PERSONAL_AUTO",
  "effectiveDate": "2026-01-01",
  "expirationDate": "2027-01-01",
  "premiumAmount": 1400.00,
  "currency": "USD"
}
```

Add collision coverage:

```json
{
  "coverageCode": "COLLISION",
  "coverageName": "Collision Coverage",
  "coverageType": "COLLISION",
  "limitAmount": 25000.00,
  "deductibleAmount": 500.00,
  "effectiveDate": "2026-01-01",
  "expirationDate": "2027-01-01",
  "exclusions": "[]"
}
```

Coverage check:

```json
{
  "claimType": "AUTO_COLLISION",
  "lossDate": "2026-06-24",
  "estimatedLossAmount": 9000.00
}
```

Submit FNOL:

```json
{
  "policyNumber": "POL-DEMO-1001",
  "claimType": "AUTO_COLLISION",
  "lossDate": "2026-06-24",
  "reportedAt": "2026-06-25T10:15:30Z",
  "lossLocation": "Columbus, OH",
  "description": "Rear-end collision at a stop light.",
  "estimatedLossAmount": 9000.00
}
```

