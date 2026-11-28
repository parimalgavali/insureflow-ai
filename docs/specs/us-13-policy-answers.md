# US-13: Answer from the selected policy

Coverage retrieval must use the selected policy exclusively. If the policy is not prepared or no supporting passage is found, explain that coverage has not been established and ask for human review. Do not silently supplement with demo terms.

Citations carry the selected policy ID, filename, page, recognized section heading and full supporting passage. Uploaded-policy prompts treat document text and filenames as untrusted data and never interpret seed product/deductible settings as proof of contract terms. A citation alone does not establish coverage. Missing wording remains a valid human-review outcome; service failures remain retryable/stale rather than masquerading as missing policy terms.

The current implementation uses scoped full-text queries with English/German incident vocabulary and common exclusion/deductible/reporting terms. It is lexical retrieval, not a guarantee of complete semantic recall. Lack of a match must never imply a claim is covered or excluded.

Older assessments must be marked stale when their source policy or readiness differs from the currently selected policy. Final submission and reviewer completion must enforce the same source check. After upload/preparation, reload canonical claim state so the customer sees the stale marker and can refresh guidance. Correction reassessment must also use the selected source.

Implementation checkpoint: source-aware schema, scoped lookup service, uploaded-policy prompt, graph retrieval/no-evidence behavior and current-source comparison helper are implemented. All 33 graph tests pass. Runtime/API wiring, stale-action guards, source/citation UI, API coverage and browser verification remain before publishing.
