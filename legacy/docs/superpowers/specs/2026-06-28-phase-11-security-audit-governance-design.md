# Phase 11 Security, Audit, And Governance Design

## Purpose

Phase 11 makes InsureFlow AI feel enterprise-ready. The goal is to add protected backend endpoints, role-aware access, request correlation, durable audit records, AI decision traceability, human override enforcement, and governance registry views.

This phase is still a portfolio/demo implementation. It should prove the architecture and behavior without requiring Azure AD, Auth0, Okta, or a production identity provider.

## Chosen Approach

Use a local HMAC-signed JWT implementation for backend tests and demos, backed by Spring Security. Add a development token endpoint that can mint short-lived demo tokens for known roles. This avoids external auth setup while keeping the API behavior close to production: clients send `Authorization: Bearer <jwt>`, roles are enforced by the backend, and the security layer can later be swapped for OAuth2 resource server validation.

Alternatives considered:

- **Full OAuth2/OIDC resource server now:** strongest production alignment, but it adds external tenant setup and secrets before cloud deployment is ready.
- **Static API keys:** simple, but it does not demonstrate role-based JWT behavior.
- **Local JWT with Spring Security:** best Phase 11 fit because it is testable, repeatable, and shows the right enterprise boundary.

## Role Model

Phase 11 uses four roles:

- `ADMIN`: full backend access.
- `ADJUSTER`: policy, claim, triage, and human review workflow access.
- `INTEGRATION`: `/integration/v1/**` access.
- `AUDITOR`: audit and governance read access.

Public endpoints:

- `/api/v1/health`
- Swagger/OpenAPI paths
- `/api/v1/auth/dev-token`

All other backend and integration endpoints require a valid JWT.

## Correlation IDs

Every request gets a correlation ID. If the client sends `X-Correlation-Id`, the backend preserves it. Otherwise, the backend generates a UUID. The ID is returned on every response and included in error responses through the existing `ApiErrorResponse.correlationId` field.

The correlation ID is also placed in logging MDC so logs can be searched consistently.

## Request Audit

Add an audit filter that records durable `audit_logs` rows for protected API requests. Each record includes:

- actor type: `USER`, `SYSTEM`, or `ANONYMOUS`;
- actor ID from the JWT subject when present;
- action from HTTP method and route;
- entity type inferred from the first route segment;
- entity ID when resolvable, otherwise a zero UUID sentinel;
- correlation ID;
- after-state JSON with method, path, status, source IP, and roles.

The audit filter should skip health, Swagger/OpenAPI, and development-token requests.

## AI Decision Audit

Persist AI triage input and output snapshots with each `ai_triage_results` row.

The input snapshot is the feature payload assembled for the triage service. The output snapshot is the triage service response: model name, model version, scores, labels, recommended queue, reason codes, explanation, and human-review flag.

This keeps the AI decision explainable without coupling the audit endpoint to the Python service runtime.

## Human Review And Overrides

Add a backend human review API:

- `POST /api/v1/claims/{claimNumber}/human-reviews`
- `GET /api/v1/claims/{claimNumber}/human-reviews`

Decisions:

- `ACCEPT_AI_RECOMMENDATION`
- `REQUEST_MORE_INFORMATION`
- `OVERRIDE_AI_RECOMMENDATION`

If the decision is `OVERRIDE_AI_RECOMMENDATION`, `overrideReason` is required and must be nonblank. Human review records link to the latest AI triage result when one exists.

The existing `human_reviews` table requires a reviewer adjuster reference. Phase 11 will add a minimal `Adjuster` entity/repository so tests and future UI/API work can create or reference adjusters cleanly.

## Governance Registry Views

Expose read-only registry endpoints:

- `GET /api/v1/governance/model-versions`
- `GET /api/v1/governance/prompt-versions`

Model and prompt registry rows already exist in the database schema. Phase 11 adds entities, repositories, DTOs, and read APIs. A small Flyway migration seeds local/demo rows for the current triage, document-intelligence, and RAG services.

## Structured Logs

Add logback configuration with a stable key-value pattern containing timestamp, level, logger, thread, correlation ID, actor ID, and message. This is not full JSON logging because the project has no JSON log encoder dependency yet, but it gives structured fields suitable for local demo and cloud log parsing.

## Error Handling

Unauthorized requests return HTTP 401. Authenticated requests without the required role return HTTP 403. Validation failures keep using the existing HTTP 400 `ApiErrorResponse` shape with correlation ID.

## Testing

Add backend tests for:

- requests without a token are rejected;
- role-specific access works for adjuster, integration, auditor, and admin roles;
- correlation IDs are returned and appear in error responses;
- protected requests write audit logs;
- AI triage persists input and output snapshots;
- human override without reason returns HTTP 400;
- human override with reason persists review and timeline/audit behavior;
- model and prompt registry endpoints return seeded rows.

## Documentation

Add `docs/api/security-audit-governance.md` covering role matrix, token generation, protected endpoints, audit behavior, governance endpoints, and local smoke-test examples.

## Out Of Scope

- External identity provider integration.
- Password login.
- Refresh tokens.
- Production secret rotation.
- Full JSON log encoder dependency.
- Rate limiting. The blueprint marks it optional, and it fits better after deployment topology is known.

## Done Criteria

- JWT-protected API behavior exists.
- Role-specific access is tested.
- Correlation IDs are returned and stored.
- Protected requests create audit records.
- AI triage decisions store input/output snapshots.
- Human override requires a reason.
- Governance registry endpoints are documented and tested.
