# US 04: Reassess saved reviewer corrections

Story: [#61](https://github.com/parimalgavali/insureflow-ai/issues/61).
Depends on US 03 / PR #90.

Saving corrections no longer completes a review. The reviewer edits the facts,
chooses **Save corrections and refresh**, checks the updated guidance and saved
field changes, then separately records the final review.

## Workflow

- The existing `edit` command validates and saves corrected facts to the workflow
  checkpoint before reassessing. It marks the previous assessment out of date.
- Reassessment reruns policy retrieval, risk scoring and answer composition using
  the corrected facts. It does not extract the old facts again from the chat.
- Successful reassessment returns to the reviewer pause with updated guidance and
  no final review decision. It does not ask the customer to submit again.
- Missing required facts, missing coverage evidence, an unavailable risk score or
  a failed answer leave corrections saved and previous guidance labeled out of date.
  Both the API and graph reject final completion until assessment succeeds.
- **Retry assessment** reruns the assessment using the saved corrections. A reviewer
  may instead request missing information from the customer.
- Retrying an identical correction returns its saved state without another model
  call. The retry also repairs a missing claim-row write after checkpoint success.
- The correction list shows changed fields with their previous and saved values.
  A structured history of all changes is covered by US 05.

## Validation and UI

Corrections validate real ISO calendar dates, HH:MM times, finite nonnegative
amounts, known event types and boolean values. Explicit nulls and false values are
applied rather than ignored. Clearing a required fact blocks reassessment until
it is supplied again. Invalid input keeps the editor and reviewer session open.
Cancel discards unsaved edits. Information requests cannot silently discard edits.

The customer view receives the refreshed risk and citations for the current claim.
Old coverage and risk badges say **Out of date** after a failure; final review is
disabled while retry and information-request actions remain available.

## Verification

Tests verify changed facts reach both retrieval and risk scoring, no fact
re-extraction occurs, each service failure preserves corrections and blocks
completion, retries recover, and invalid inputs or combined correction/completion
requests are rejected. Frontend checks cover stale labels, saved field changes,
draft preservation and refreshed displayed risk. The end-to-end flow rejects an
invalid correction, saves a valid one, checks refreshed guidance and only then
completes the review.
