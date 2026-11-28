# US-12: Prepare uploaded policy text for searching

Customers can prepare an uploaded policy for search. Preparation keeps PDF page numbers and recognized numbered/lettered section headings, stores bounded passages against the exact policy and conversation, and makes those passages searchable with a scoped full-text index.

The processor runs in a separate process with a 30-second deadline, CPU limit, and an address-space limit where supported. It accepts at most 300 pages and 2 million extracted characters. Passages are at most 1800 characters and never cross a page boundary. Heading detection is a text heuristic; it does not reconstruct arbitrary visual layouts or guarantee semantic completeness.

An encrypted, unreadable, empty or over-limit PDF fails with a clear error and no ready passages. Nonempty pages without enough readable text are rejected rather than silently omitted; truly blank spacer pages are allowed. There is no OCR in this story. Preparation status becomes ready only when passages and counts commit together. Failed work can be retried; completed work is reused. Concurrent preparation uses a policy-scoped lock and does not hold a database transaction while parsing.

PolicyPassage has a composite foreign key binding each passage to its policy and conversation. Search requires both IDs and a ready policy. Full-text search uses the simple dictionary to retain English/German terms; semantic and cross-language retrieval integration is a separate concern. Coverage still uses standard demo wording until story 13.

Implementation checkpoint: worker extraction, status endpoint, page/heading metadata, searchable storage and scope filtering are implemented. Five policy API checks and three worker failure checks pass. Processing UI, broader recovery/concurrency verification, full suites and final review remain before publishing.
