# legacy/ — InsureFlow AI v1 (archived)

This folder is the v1 codebase, frozen as of tag `v1-guidewire-prototype` (June–July 2026).

v1 was a Guidewire-inspired, multi-service prototype: Spring Boot API, three FastAPI "AI" services, a Vue adjuster workbench, a synthetic data generator, Compose/Azure/Prometheus packaging and ~16k lines of phase documentation.

It is kept here for one release so the code stays browsable, but **it is not maintained and does not run as part of v2**. Its GitHub Actions workflows were moved to `legacy/.github/workflows/` so they no longer execute.

Why it was retired (full audit in `../docs/planning/2026-10-27-v2-direction.md`):

- All data was self-generated synthetic data; no public or real dataset was ever wired in.
- The "RAG", "document intelligence" and "ML triage" components were deterministic keyword/regex logic and a model trained on rule-generated labels — not real AI.
- Breadth (9 containers, 5 pages, 20 phases) hid the lack of depth.

v2 narrows the project to one real loop: file a motor claim by conversation, grounded in real policy wording and a model trained on real claims. See the root `README.md`.
