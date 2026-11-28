# US 06: Customer claim-summary corrections

Story: [#63](https://github.com/parimalgavali/insureflow-ai/issues/63).
Depends on US 05 / PR #92.

Customers can edit collected facts while collecting information, before their first
submission, or when responding to an information request. The editor shows missing
details and explains invalid calendar dates, times and negative amounts. Invalid
changes are rejected by both UI and API, and the draft remains available to fix.

## Workflow

- `PATCH /api/claims/{id}/facts` uses ordinary customer access and accepts only a
  validated facts patch. It cannot set reviewer identity, review status or risk.
- The workflow applies the typed corrections directly. If required details are
  still missing, it stays in collection and lists them. Otherwise it reruns policy
  retrieval, risk scoring and composition before returning to the submission pause.
- If assessment fails, edits remain saved, guidance is marked as needing refresh,
  and both API and graph block submission. `POST /api/claims/{id}/facts/refresh`
  retries using the saved facts.
- Customer edits cannot change an awaiting-review or completed claim. Reviewer
  corrections continue through their separate authorized action and return to the
  reviewer pause, never to customer submission.
- Changes are included in the workflow conversation as confirmed customer facts.
  The saved conversation and history record the correction and assessment once;
  identical retries recover checkpointed results without another model call or
  duplicate messages. A failed claim-row commit is recoverable on retry.
- Unsaved drafts disable submission. Cancel discards the draft. Yes/no and incident
  selections offer plain-language choices; blank required details remain missing.
- A partial claim with no prior assessment does not claim that a policy search failed.

## Verification

Agent checks cover edits during collection, direct assessment of corrected facts,
missing details, failures and customer/reviewer pause boundaries. API checks cover
validation, access, retries, persisted facts/messages/history, failed-write recovery,
and rejection after submission. Frontend checks cover inline errors, draft cancel,
stale submission blocking and retrying the correct action. The end-to-end flow edits
facts before submission, rejects invalid input, refreshes guidance, completes the
reviewer flow and verifies saved history after a reload.
