# US 05: Saved claim history

Story: [#62](https://github.com/parimalgavali/insureflow-ai/issues/62).
Depends on US 04 / PR #91.

Customers and reviewers can see an ordered record of submissions, requests for
information, saved fact changes, assessment outcomes and completed reviews. Review
entries include the available access role, decision, optional note and recorded
server time. Shared reviewer credentials are labeled as shared demo access, not
as a named person.

## Persistence and retries

- Migration 0004 creates `claim_events`. Each entry belongs to one claim; the
  application exposes read-only history and records new events with claim writes.
- Server event IDs preserve action order. Timestamps are timezone-aware; submission
  entries use the actual recorded submission time.
- Submission and reviewer operation IDs are generated inside the workflow and
  checkpointed. A per-claim operation/kind constraint prevents retries or recovered
  writes from recording duplicate events. Each real resubmission gets a new ID.
- Correction entries use only the changes made by that action. A recheck with
  unchanged values does not repeat the earlier correction as if it happened again.
- Notes and role identities come from validated reviewer actions and access checks.
  Clients cannot supply event times, event identities or reviewer names.
- Earlier activity is not reconstructed from guessed dates. The history explains
  that activity before this feature may be unavailable.

## UI and access

The claim card shows history and a stable **Open saved history** link. The history
URL can be reloaded without creating a new conversation. It uses the existing claim
access rules; private customer accounts remain outside the demo's current scope.
If access requires a credential, the history page supports entering it again and
keeps it only in memory until the page is left.
History notes render as plain text. Failed or superseded loads clear old entries.

Reviewers can add an optional note to corrections or final review. Existing
information-request notes are recorded as well. The current customer view updates
its history when an action changes that claim.

## Verification

API checks cover complete ordered history, notes, role identity, changed fields,
read access, unavailable claims, read-only endpoints, retries, failed-write recovery
and unchanged-value rechecks. Frontend checks cover safe note rendering, role labels,
saved-history navigation, loading errors and late responses. The end-to-end flow
finishes a reviewed claim, opens saved history, reloads, and verifies the same actions
and review note remain available.
