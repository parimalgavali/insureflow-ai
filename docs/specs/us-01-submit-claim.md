# US 01: Customer submission before human review

Story: [#58](https://github.com/parimalgavali/insureflow-ai/issues/58).

The assistant prepares an assessed claim. The customer sees **Ready to submit** and
chooses **Send to adjuster**. This action moves the claim to **Awaiting adjuster**;
it does not create a review decision or ask for the reviewer credential.

An authorized reviewer uses the separate **Record adjuster review** action. The
existing review endpoint remains protected by the adjuster credential. A reviewer
cannot complete a new claim before the customer submits it.

## State flow

`collecting → assessed → awaiting_review → reviewed`

The agent checkpoints separate submission and review interrupts. Customer chat is
paused once assessment is complete so ordinary messages cannot bypass either
handoff. Customer correction and further-information flows have separate stories.

`POST /api/claims/{id}/submit` uses the existing customer access rules. A database
row lock serializes submissions for a claim. Retrying a submitted or reviewed
claim returns its saved state without another graph run or review. If checkpoint
persistence succeeds before a database failure, a retry uses the checkpointed
submission to repair the saved claim state.

## Verification

- Agent tests check both pauses and review-before-submission rejection.
- API tests cover concurrent submissions, retries, access checks and saved states.
- Frontend tests distinguish submission from review and check the busy state.
- The existing end-to-end flow submits before recording an authorized review.
- Existing pending review checkpoints remain on the unchanged `human_review` node.
