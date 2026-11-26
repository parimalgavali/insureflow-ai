# US 03: Reviewer requests for more information

Story: [#60](https://github.com/parimalgavali/insureflow-ai/issues/60).
Depends on US 02 / PR #89.

An authorized reviewer can write a clear request for missing information instead
of completing the review. The claim becomes **Information needed**, leaves the
pending-review queue, and displays the request to the customer. The request is
also saved in the conversation with an explicit reviewer label.

The customer can reply in the existing chat. The assistant extracts the new
details, refreshes the assessment, and stops at **Ready to submit**. The customer
must submit again before a reviewer can complete the review.

## Rules

- Information requests need a nonblank note, up to 2,000 characters. They cannot
  combine a fact correction with a request for information.
- The information-request decision does not set the claim to reviewed.
- A customer cannot resubmit before replying and reaching a new assessment.
- Old guidance and review details are cleared when a new collection round starts.
- Review actions hold the claim row lock, preventing concurrent reviewers from
  sending duplicate requests. Only an exact checkpointed decision is recoverable
  after a failed database commit, without rerunning the graph or duplicating the
  saved request.
- Resubmission records the new submission time. The earlier request remains in
  the conversation; a structured history is covered by US 05.

## Verification

Agent and API tests cover note validation, access, simultaneous requests, persisted
requests, customer replies, mandatory resubmission, and a database commit failure.
Frontend tests cover the separate request action, customer instructions and
clearing outdated guidance. The end-to-end scenario requests information, returns
to the customer, replies, resubmits, and completes an authorized review.

`hit_and_run_followup.json` extends the original recorded scenario with explicitly
labeled synthetic replies for the additional test turn. No paid AI calls are
required by these checks.
