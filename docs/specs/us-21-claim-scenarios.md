# US-21: Test the main types of car insurance claims

The repeatable suite now covers collision, theft, windscreen glass damage, vandalism and storm/hail damage. Each has a matching-product case and a liability-only exclusion case under a clearly fictional selected policy: ten complete API workflows, plus a policy/scenario inventory check.

Every workflow uploads and prepares the real six-page test PDF, then runs two recorded customer turns. The first turn leaves the incident date unknown and must stay Collecting, ask a follow-up, skip scoring and reject premature submission/review. The second turn must preserve earlier facts, fill the supplied date/risk details and produce the expected complete card. Unknown theft/vandalism times remain null.

The suite checks exact saved facts, selected product/deductible, supporting policy passage/page/filename/document ID, coverage status, requested documents and saved checklist states. Actual scoped PostgreSQL full-text search is used. A demo-retrieval guard fails if the selected policy falls through to shared wording. The composition input must contain the retrieved source excerpt; the final citation must reference that same policy and page.

Submission must produce Awaiting review with no adjuster decision, remain idempotent and preserve facts/checklist state. The authorized reviewer must be able to open the identical saved handoff. Customer-only review is rejected; only a subsequent explicit adjuster action can produce Reviewed. Submitting/reviewing must not make extra model/scorer calls or duplicate history.

All completions use committed RecordedProvider fixtures. Live Anthropic/Ollama completions are guarded against, and the tests remove any Anthropic key from their scoped environment. The scorer is a controlled input-recording probe that verifies gating and passed facts. This is a workflow contract suite, not evidence of live model accuracy, trained risk-model performance or actual insurance coverage. No product behavior or public UI is changed by this story.

The fictional policy's six pages were rendered and visually inspected. The scenario fixtures contain only synthetic narratives and documents. The tests run in the existing Python CI job and require no new paid service or workflow configuration.

Checkpoint validation: all 11 new scenario checks and the full 225-test backend suite passed before final fixture/test refinements. Final review added explicit product/deductible and complete composer-fact input assertions, and adjusted recorded explanations to include the policy filename/page. Lint, formatting and the policy/matrix inventory check passed afterward. The final database rerun was not executed because automatic approval review reached its usage limit; rerun the scenario module before publishing the PR.
