# US-15: Keep policy searches separate for each claim

Policy lookup selects only the current document for the conversation. Full-text search filters both the passage and document conversation IDs, the selected document ID, readiness and current-version status. Superseded versions cannot enter a new coverage search.

Citations are embedded in authenticated claim/conversation responses, with no public passage-download route. Policy metadata, upload, preparation, replacement, message and claim endpoints use the same demo access rule. This shared credential is not private account ownership: an authorized demo reader can read either saved claim by ID, and explicitly open demo mode permits access without a token.

A composite, deferred foreign key also prevents revision chains from linking policies in different conversations. It permits deletion of a whole conversation and its retained versions while preserving unrelated claims.

Completed message responses stay bound to conversation plus operation ID. When replaying a response after policy selection changes, its historical card and question carry an explicit out-of-date warning; saved provenance is retained without mutating the cached response or calling the model again. Late policy metadata responses cannot overwrite another displayed conversation.

Validation: 157 backend tests, 66 frontend tests, type check, build, lint and formatting pass. Two-claim tests use identical filenames, passage IDs, incident facts and retry operation IDs but distinct sentinel wording. They prove separate model inputs, answer passages, citations, saved messages and response caches, including configured-token checks. Database tests reject cross-conversation revision links and verify unrelated claims survive scoped deletion. Existing recorded browser flow is also checked. There is no new private-account or ownership authorization in this story.
