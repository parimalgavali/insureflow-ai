# US-13: Answer from the selected policy

Coverage retrieval must use the selected policy exclusively. If the policy is not prepared or no supporting passage is found, explain that coverage has not been established and ask for human review. Do not silently supplement with demo terms.

Citations carry the selected policy ID, filename, page, recognized section heading and full supporting passage. Uploaded-policy prompts treat document text and filenames as untrusted data and never interpret seed product/deductible settings as proof of contract terms. A citation alone does not establish coverage. Missing wording remains a valid human-review outcome; service failures remain retryable/stale rather than masquerading as missing policy terms.

The current implementation uses scoped full-text queries with English/German incident vocabulary and common exclusion/deductible/reporting terms. It is lexical retrieval, not a guarantee of complete semantic recall. Lack of a match must never imply a claim is covered or excluded.

Older assessments must be marked stale when their source policy or readiness differs from the currently selected policy. Final submission and reviewer completion must enforce the same source check. After upload/preparation, reload canonical claim state so the customer sees the stale marker and can refresh guidance. Correction reassessment must also use the selected source.

Implemented and self-reviewed. Runtime/API wiring, source-aware citation display and stale-action guards are complete. The policy panel reloads canonical state after upload/preparation. Preparation is restricted to pre-submission conversations without pending messages; claim actions lock the selected policy and reject processing work.

Validation: 149 backend tests, 63 frontend tests, type check, build, lint and formatting passed. Tests cover selected-policy answers, missing wording, customer/reviewer refreshes, stale submission/review guards and preserving retry semantics. The browser flow uploads and prepares a synthetic three-page policy, verifies filename/page/full-passage citations and completes corrections, review and saved history. Recorded compositions are explicitly labelled synthetic; this is not a live-model quality evaluation. Review also fixed body sentences starting with “A” being misclassified as section headings.
