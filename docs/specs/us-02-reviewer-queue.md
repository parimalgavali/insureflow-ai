# US 02: Protected reviewer queue

Story: [#59](https://github.com/parimalgavali/insureflow-ai/issues/59).
Depends on US 01 / PR #88.

Reviewers open the **Reviewer queue** link and enter the existing reviewer token.
The queue lists claims awaiting review, oldest submitted first, with their
submission times. Selecting one shows the existing claim card with facts,
coverage references and risk reasons. Review controls appear only in this
workspace; customer submission stays on the customer screen.

## Access and persistence

- Both queue and reviewer detail endpoints require the reviewer credential.
  Customer credentials cannot read them or record a review.
- The reviewer token stays in component memory. Locking or leaving the workspace
  clears credentials and protected data. Late responses after locking are ignored.
- Migration 0003 adds nullable `claims.submitted_at` and a queue index. Customer
  submission sets the time once; retries preserve it. Historical records keep null
  and display an unavailable date rather than a made-up submission time.
- The queue is paged (20 by default, up to 100 per request) and can be refreshed.
- A completed review refreshes the queue and updates the current customer claim
  if it is open in the same app session.

## Verification

API checks cover role separation, ordering, page limits, selected claim evidence,
missing records, and submission timestamps. Frontend checks cover credential
failure, paging, unknown dates, selection, review, and late responses after locking.
The end-to-end flow submits a claim, rejects invalid queue access, reviews with
the reviewer credential, locks the workspace, and returns to the customer view.
