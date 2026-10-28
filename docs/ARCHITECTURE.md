# Architecture (v2)

Principle: one process per language, one database, one screen. Everything a reviewer wants to see is reachable in two clicks from the repo root.

## Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│ web/  (Vue 3 + Vite + TypeScript, one route)                            │
│   Chat column: messages, streaming tokens, follow-up chips, upload      │
│   Claim card: facts · coverage verdict + citations · risk signal ·      │
│               missing documents · "Send to adjuster"                    │
└──────────────┬──────────────────────────────────────────────────────────┘
               │ REST + SSE (/api)
┌──────────────▼──────────────────────────────────────────────────────────┐
│ api/  (FastAPI, Python 3.12)                                            │
│   routers/      conversations, messages (SSE), claims, review, health   │
│   agent/        LangGraph graph, state schema, nodes, prompts           │
│   rag/          retriever (pgvector), citation formatting               │
│   ml/           model loader, feature mapping, explainer                │
│   llm/          Provider protocol → AnthropicProvider | OllamaProvider  │
│   db/           SQLAlchemy models, Alembic migrations                   │
└──────┬──────────────────────┬───────────────────────────┬───────────────┘
       │                      │                           │
  Postgres 16 + pgvector   model artifact (.joblib)    LLM (Anthropic API
  conversations, messages, from ml/ training          or local Ollama)
  claims, policy_chunks,
  langgraph checkpoints
```

Offline training / ingestion live beside the API but are not part of its runtime:

- `ml/` — `train.py`, `evaluate.py`, notebook, `model_card.md`, writes `artifacts/fraud_model.joblib` (git-ignored; CI retrains on a cached dataset or downloads a release artifact).
- `rag/` — `ingest.py` (PDF → clause chunks → embeddings → `policy_chunks`), `eval/questions.jsonl`, `eval.py`.
- `scripts/fetch_data.py` — downloads everything in `docs/DATA.md`.

## The agent (LangGraph)

```
            ┌────────────┐
 user msg ─►│  extract   │  LLM, structured output → ClaimFacts (partial allowed)
            └─────┬──────┘
                  ▼
            ┌────────────┐   missing required facts?
            │check_missing├──────────yes──────► ask_followup ──► (END, wait for user)
            └─────┬──────┘
                  │ no
                  ▼
            ┌────────────┐
            │retrieve    │  question built from facts → pgvector top-k AKB clauses
            └─────┬──────┘
                  ▼
            ┌────────────┐
            │score_risk  │  facts → Kaggle feature schema → model → score + top reasons
            └─────┬──────┘
                  ▼
            ┌────────────┐
            │compose     │  LLM: grounded coverage answer citing clause ids + plain-language summary
            └─────┬──────┘
                  ▼
            ┌────────────┐
            │human_review│  interrupt(); resumes when reviewer accepts/edits
            └────────────┘
```

- **State** (`AgentState`): messages, `facts: ClaimFacts`, `missing: list[str]`, `retrieved: list[Chunk]`, `risk: RiskSignal | None`, `card: ClaimCard | None`, `language: "de" | "en"`.
- **Checkpointer:** `PostgresSaver`; `thread_id` = conversation id, so a conversation survives restarts and the interrupt can resume days later.
- **Grounding rule:** `compose` may only state coverage facts that appear in `retrieved`; if the top score is below a threshold it says so and lists what evidence would help. Tested with recorded LLM responses.
- **Determinism for tests:** every LLM call goes through `Provider.complete(messages, schema)`; tests use a `RecordedProvider` that replays JSON fixtures.

## Retrieval

- Chunking: split AKB on its clause numbering (`A.2.3.2`, `E.1.1.3` …) rather than fixed windows; each chunk keeps `clause_id`, `title`, `parent` and `page`.
- Embeddings: multilingual sentence-transformer (small, CPU-friendly), stored as `vector(384)`; HNSW index.
- Query: the user's own words + up to three German policy-language rewrites from the LLM (`rag/query_rewrite.py`; EN→DE translation and colloquial→wording rephrase, e.g. "zerkratzt" → "mut- oder böswillige Handlungen"); union of results ranked by best cosine score; top-5 with `clause_id`. Rewrites for the eval set are recorded in `rag/eval/rewrites.json` so eval/CI run without an API key.
- Evaluation: `rag/eval/questions.jsonl` — hand-written DE/EN questions with expected clause ids; `rag/eval.py` reports top-1/top-3 hit rate. Target ≥ 0.8 top-3.

## ML

- Model: `HistGradientBoostingClassifier` (handles categoricals, fast), class weighting, stratified 5-fold CV, held-out test.
- Metrics that matter on a 6% positive rate: AUPRC, recall at precision ≥ 0.5, calibration curve. Accuracy is reported but called out as misleading.
- Excluded features: `Sex`, `MaritalStatus`, `Age`, `AgeOfPolicyHolder` (fairness); `PolicyNumber`, `RepNumber` (leakage/ids).
- Explanation: per-prediction feature contributions (permutation-based or SHAP if dependency weight is acceptable) → top-3 reasons in plain language.
- Serving: load artifact once at startup; `predict(facts) -> RiskSignal(score, band, reasons)`.

## API (sketch)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/conversations` | start; returns id + greeting |
| POST | `/api/conversations/{id}/messages` | user message (+ optional file); **SSE** stream of agent events: `token`, `facts`, `citations`, `risk`, `card`, `question`, `done` |
| GET | `/api/conversations/{id}` | full state for reload |
| POST | `/api/claims/{id}/review` | reviewer accept/edit → resumes the interrupted graph |
| GET | `/api/health` | db, model, provider status |

Auth is intentionally minimal for a demo (single demo user; bearer token from env). Stated in the README.

## Frontend

One route. Left: message list with streaming assistant text and follow-up chips rendered from `question` events. Right: `ClaimCard` that fills in as `facts`/`citations`/`risk`/`card` events arrive. Citations open a popover with the clause text and id. Mobile: card collapses under the chat. Vitest for components; one Playwright smoke test for the happy path.

## Deployment

`docker-compose.yml`: `db` (postgres:16 + pgvector), `api`, `web` (nginx serving the built SPA and proxying `/api`). `.env.example` lists `ANTHROPIC_API_KEY`, `LLM_PROVIDER=anthropic|ollama`, `DATABASE_URL`. CI: ruff + pytest for `api/`, `ml/`, `rag/`; vitest + build for `web/`; Playwright smoke against compose.

## What is deliberately absent

Message queues, metrics stacks, cloud templates, role matrices, multi-tenancy, model registries. Each can be added later as a one-PR task if a job description demands it; none earns its complexity in a one-screen demo.
