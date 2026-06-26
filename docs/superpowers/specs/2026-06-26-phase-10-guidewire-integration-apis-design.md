# Phase 10 Guidewire Integration APIs Design

## Purpose

Phase 10 demonstrates Guidewire-style system-to-system integration thinking. The goal is to expose a stable `/integration/v1` namespace for upstream or downstream systems without duplicating the existing policy and claim business workflows.

The integration layer should look like an enterprise adapter: it accepts external reference IDs, delegates to the core domain services, records integration events, returns consistent envelopes, and leaves deeper security/governance controls to Phase 11.

## Chosen Approach

Use a Spring Boot integration facade over the existing policy and claim services.

Alternatives considered:

- Build separate integration-only domain flows. This would be realistic for a large enterprise system but would duplicate rules already implemented in Phases 3 and 4.
- Add only documentation and Postman examples. This would satisfy part of the blueprint but would not demonstrate backend integration design.
- Use a facade with a small integration event log. This is the best Phase 10 fit because it keeps behavior testable, shows adapter-layer thinking, and preserves existing workflow rules.

## API Scope

All Phase 10 endpoints live under `/integration/v1`.

- `POST /integration/v1/policies/sync`: create or activate a policy from an external policy payload.
- `POST /integration/v1/claims`: create a claim using the existing FNOL workflow.
- `GET /integration/v1/claims/{claimNumber}`: return a claim lookup response with policy and coverage context.
- `POST /integration/v1/claims/{claimNumber}/status`: update claim status through the existing workflow service.
- `POST /integration/v1/claims/{claimNumber}/reserves`: record a reserve update for a claim.
- `POST /integration/v1/webhooks/claim-triaged`: simulate an outbound/inbound claim-triaged event webhook acknowledgement.

## Persistence

Phase 10 adds two small persistence concepts:

- `integration_events`: records external system name, event type, external reference, status, payload, and optional linked claim number or policy number.
- `claim_reserves`: records reserve amount, currency, coverage code, reason, source system, and external reserve reference for a claim.

The integration event log is not the full enterprise audit layer. It is an integration-facing operational ledger. Phase 11 can add authenticated users, correlation IDs, structured security audit, and AI governance audit.

## Data Flow

Policy sync validates the external payload, creates the customer when requested through the request payload, creates the policy through `PolicyManagementService`, adds coverage rows, optionally activates the policy, and writes an integration event.

Claim create delegates to `ClaimIntakeService.submit`, preserving coverage validation and claim-number generation. It writes an integration event with the external claim reference.

Claim status update delegates to `ClaimWorkflowService.changeStatus`, preserving allowed transition rules. It writes both the existing claim timeline event and an integration event.

Reserve update writes a `ClaimReserve` and records a `RESERVE_UPDATED` claim timeline event plus an integration event.

Webhook simulation stores the received claim-triaged event and returns an acknowledgement with `accepted=true`.

## Error Handling

The integration layer uses the existing global exception handling:

- validation failures return HTTP 400;
- missing policy or claim references return HTTP 404;
- invalid workflow transitions return HTTP 422;
- successful creations return HTTP 201 where a new integration resource is created.

Responses should be simple JSON records, not custom wrappers, to stay consistent with the existing API style.

## Testing

Add backend integration tests that prove:

- policy sync creates a customer, policy, coverage, and integration event;
- claim create uses existing FNOL behavior and returns a claim number;
- invalid status transitions still return HTTP 422;
- valid status updates create timeline events;
- reserve updates persist and create a claim timeline event;
- webhook simulation stores an integration event and returns an acknowledgement;
- bad payloads return consistent validation errors.

## Documentation

Add `docs/api/integration-apis.md` with endpoint contracts and example payloads. Add an HTTP collection under `docs/api/collections/phase-10-integration-apis.http` so the flow can be replayed from an IDE or imported into Postman-style tooling.

## Out Of Scope

- JWT authentication and role enforcement.
- Full audit logging aspect/interceptor.
- AI decision audit persistence.
- Human override reason enforcement.
- Real external Guidewire connectivity.
- Idempotency keys and replay protection beyond recording external references.

Those belong in Phase 11 or later hardening phases.

## Done Criteria

- `/integration/v1` endpoints are implemented and tested.
- Claim reserve updates persist.
- Integration events persist for Phase 10 integration actions.
- Documentation and HTTP collection are committed.
- `PROJECT_MEMORY.md` records Phase 10 start/completion evidence.
