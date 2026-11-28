# US-22: Test unclear and changing answers in English and German

Four controlled API scenarios cover English, German and both language-switch directions. Competing dates and amounts stay null until confirmed; an "I don't know" / "Ich weiß nicht" reply leaves the missing fields unknown. Questions ask for the missing date and other-party involvement, and premature submission remains blocked. Stable incident descriptions are retained across language switches rather than silently translated or replaced.

Once core facts are supplied, the recorded answer reports conflicting evidence. The card must be Unclear even when the model's proposed status was likely covered. Unknown witnesses mean no risk signal and no scorer call. The selected policy's real prepared passages remain the citation source.

Explicit customer corrections change the date from 24 to 25 October and the estimate from EUR 1800 to EUR 900, refresh guidance with the current facts, and record exact before/after values. Invalid date/amount inputs save nothing and make no model call. A subsequent explicit Not known correction clears a previously confirmed witness value, removes the risk signal and forwards null into the refreshed composition.

Conversation language, messages, current facts and history are checked after reloading saved responses. The composition prompt must use the target language. Vue tests restore an existing conversation and switch its language while keeping the same saved ID and original transcript; only the next message adopts the new language. A language toggle does not create another claim.

Completions and questions are committed RecordedProvider fixtures; the risk scorer is a controlled probe. This tests state handling, persistence and language routing against known responses, not a live model's understanding/translation quality or actual coverage. The natural-language unknown cases begin with unconfirmed values; retracting a known field is tested through the explicit correction API rather than claiming arbitrary prose is always interpreted correctly. No product behavior changes were necessary.

Final validation: all 229 backend tests and 86 frontend tests passed, along with lint, formatting and whitespace checks. Self-review made the UI language tests restore a real saved-conversation shape rather than manually replacing store fields. No unresolved findings remain.
