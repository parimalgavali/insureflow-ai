# US-14: Replace the wrong policy and refresh guidance

Customers can replace the current policy before submitting the claim, after explicitly confirming the selected filename. Replacements create a new revision rather than overwriting older policy records. Exactly one revision is current per conversation.

Replacement requests carry the ID being replaced. An identical retry returns the new selection, while a competing request with an obsolete ID is rejected. Invalid PDFs or failed database writes preserve the existing selection and remove uncommitted files. Replacement waits for message and policy processing to finish.

Superseded passages remain attached to their historical document but are excluded from coverage search. Current-policy lookup and assessment freshness checks use only the current revision. A replacement that is unprepared or failed always keeps guidance stale, even if the customer attempts an assessment refresh. Processing success alone is insufficient: the assessment must then be refreshed against the new policy before submission. Failed preparation never silently reuses old guidance.

Existing access rules apply. Replacement is unavailable after submission. Stored historical versions are retained for the claim lifecycle; downgrade refuses to discard them automatically.

Implementation checkpoint: migration 0008, versioned PUT endpoint, source/search guards and failure recovery are implemented. Targeted API checks verify revision/idempotency, obsolete IDs, rollback safety, failed preparation remaining stale, successful preparation plus reassessment, and rejection after submission. Filename-confirmation UI, concurrency/browser verification and final review remain before publishing.
