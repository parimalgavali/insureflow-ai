# Task 7 — Quality & release

**Goal:** a stranger clones the repo, runs one command, and has the demo in two minutes; CI proves the happy path.

**Deliverables**
- Playwright smoke test (`web/e2e/`) against the compose stack with `LLM_PROVIDER=recorded`: open page → send scripted message → answer follow-up → card shows citation + risk → send to adjuster.
- `make demo` / `scripts/demo.sh`: fetch data (cached), ingest AKB, train or download the model artifact, `docker compose up`.
- Model artifact distribution: GitHub Release asset or CI-trained-and-cached; README explains both.
- README: 60-second GIF of the flow, "run it" section verified on a clean machine, metrics table lifted from the model card, RAG eval numbers.
- `docs/portfolio/`: 5 resume bullets, 10 interview Q&A (incl. "what would break in production?"), a one-paragraph LinkedIn post.
- Security hygiene: `.env` never committed, demo token documented, upload size/type limits, dependency audit in CI.

**Done when:** CI runs unit + e2e green on `main`; a fresh VM reproduces the demo from the README alone.

**Risks:** e2e flakiness — run against recorded provider only; GIF size — keep < 5 MB.
