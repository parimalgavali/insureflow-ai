# Security, Audit, And Governance

Phase 11 adds the first operational guardrails around the InsureFlow AI backend: JWT authentication, role-based authorization, correlation IDs, audit trails, AI decision snapshots, governance registries, and human review override enforcement.

## Roles

The backend accepts HMAC-signed JWT bearer tokens with these roles:

| Role | Access |
| --- | --- |
| `ADMIN` | Full backend and integration access. |
| `ADJUSTER` | Core `/api/v1` claim and policy workflow access. |
| `AUDITOR` | Audit and governance registry read access. |
| `INTEGRATION` | `/integration/v1` system integration access. |

For local development and tests, tokens can be minted through:

```http
POST /api/v1/auth/dev-token
Content-Type: application/json

{
  "subject": "demo-adjuster",
  "roles": ["ADJUSTER"]
}
```

Use the returned token as:

```http
Authorization: Bearer <token>
```

## Correlation IDs

Every request receives an `X-Correlation-Id` response header. If the caller sends one, the backend preserves it. If not, the backend generates a UUID. Error responses also include the same correlation ID so logs, audit records, and API responses can be tied together.

## Audit Trail

Protected backend requests are written to `audit_logs` with:

- actor type and actor ID
- request action
- inferred entity type
- correlation ID
- request path, method, status, and source IP

Auditors and admins can inspect audit records by entity:

```http
GET /api/v1/audit/entity/{entityType}/{entityId}
Authorization: Bearer <AUDITOR or ADMIN token>
```

Phase 11 uses the nil UUID `00000000-0000-0000-0000-000000000000` for request-level audit records that are not yet tied to a specific domain row.

## AI Decision Snapshots

Claim triage now stores both the request features and the model response in `ai_triage_results`:

- `input_snapshot`
- `output_snapshot`

This keeps the AI recommendation reproducible enough for portfolio governance demos, audits, and future review screens.

## Governance Registry

Phase 11 seeds read-only registry data for model and prompt versions.

```http
GET /api/v1/governance/model-versions
Authorization: Bearer <AUDITOR or ADMIN token>
```

```http
GET /api/v1/governance/prompt-versions
Authorization: Bearer <AUDITOR or ADMIN token>
```

These endpoints are intentionally auditor/admin only because they expose operational metadata rather than claim workflow data.

## Human Review

Human review decisions can be recorded against a claim:

```http
POST /api/v1/claims/{claimNumber}/human-reviews
Authorization: Bearer <ADJUSTER or ADMIN token>
Content-Type: application/json

{
  "reviewerAdjusterId": "11111111-1111-1111-1111-111111111111",
  "decision": "OVERRIDE_AI_RECOMMENDATION",
  "overrideReason": "Evidence in the uploaded medical note contradicts the triage reason code.",
  "notes": "Senior adjuster reviewed the supporting documents."
}
```

When the decision is `OVERRIDE_AI_RECOMMENDATION`, `overrideReason` is required. The backend links the review to the latest triage result when one exists and writes a claim timeline event.

Human review history can be read with:

```http
GET /api/v1/claims/{claimNumber}/human-reviews
Authorization: Bearer <ADJUSTER or ADMIN token>
```

## Logging

`logback-spring.xml` emits structured key/value logs with `correlationId` and `actorId` MDC fields. This is enough for local demos and gives Phase 12 deployment work a straightforward path into cloud log search.
