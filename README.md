# InsureFlow AI — ClaimPilot

**File a motor insurance claim by talking to it.** One screen: a chat on the left, a live claim card on the right. An agent extracts the facts, asks for what is missing, checks coverage against the *real* policy wording with clause citations, scores fraud risk with a model trained on *real* claims, and hands the result to a human reviewer.

> Portfolio project by Parimal Gavali. Backend engineering + frontend engineering + applied AI, each backed by something you can open and read. Decision support only — nothing here approves, denies or accuses.

**Status:** v2 in progress. The v1 prototype is archived under [`legacy/`](legacy/README.md) (tag `v1-guidewire-prototype`). Current step: see [docs/ROADMAP.md](docs/ROADMAP.md).

---

## What it does

Real transcript (German input, recorded LLM responses; `make e2e` replays exactly this):

```
You:   Gestern Abend hat jemand mein geparktes Auto auf dem Supermarktparkplatz in Köln
       angefahren und ist einfach weggefahren. Die hintere Stoßstange ist eingedrückt.
Agent: Das tut mir leid. Damit ich den Fall einordnen kann: Wann genau ist das passiert,
       und wurde die Polizei informiert?
You:   Das war am 25.10.2026 gegen 19 Uhr. Die Polizei habe ich nicht gerufen, Zeugen gab es keine.
Agent: Nach den Musterbedingungen ist ein Unfallschaden am eigenen Fahrzeug in der Vollkasko
       versichert [A.2.2.2.2]; dazu zählt auch, wenn ein Unbekannter Ihr geparktes Auto
       beschädigt. Ihre vereinbarte Selbstbeteiligung wird abgezogen [A.2.5.8]. Bitte beachten
       Sie Ihre Pflichten im Schadenfall: Schaden innerhalb einer Woche anzeigen [E.1.1.1] und
       alles zur Aufklärung beitragen [E.1.1.3]. Ein Sachbearbeiter prüft den Fall.
Card:  hit_and_run · Köln · 2026-10-25 19:00 · third party unknown · police report: no
       Coverage: likely covered (4 cited clauses, click to read)   Risk: low (model hgb-v1)
       Please provide: Polizeibericht/Anzeigenummer, Fotos, Kostenvoranschlag
       [Send to adjuster] → status "Reviewed by adjuster"
```

Every sentence above maps to a component:

| Piece | What is behind it |
| --- | --- |
| Follow-up questions | A **LangGraph** state graph with a conditional loop: `extract → check_missing → ask / continue` |
| Coverage with citations | **RAG** over the GDV *Allgemeine Bedingungen für die Kfz-Versicherung (AKB 2015)* — real German motor policy wording, clause-chunked, embedded with a multilingual transformer, stored in **pgvector** |
| Risk signal with reasons | A **scikit-learn** gradient-boosting model trained on 15,420 real vehicle claims (Kaggle vehicle-insurance-fraud, CC0), evaluated as an imbalanced problem (AUPRC, recall at fixed precision), with per-prediction feature contributions |
| "Send to adjuster" | A LangGraph **human-in-the-loop interrupt**; the conversation state is checkpointed in Postgres |
| The LLM | Anthropic Claude via a provider interface; **Ollama** fallback so the demo runs offline |
| Bilingual | Corpus is German, UI is English, user may write either; multilingual embeddings handle DE↔EN retrieval |

## Architecture

```
Browser — Vue 3 single page (chat + claim card)
   │ HTTP + Server-Sent Events
   ▼
FastAPI ─── LangGraph agent (in-process) ─── LLM provider (Anthropic | Ollama)
   │              │              │
   │              │              └── fraud model artifact (.joblib) + explainer
   │              └── retriever ──► Postgres + pgvector (policy_chunks)
   └── SQLAlchemy ───────────────► Postgres (conversations, messages, claims, checkpoints)
```

Three containers: `db`, `api`, `web`. Details in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Data

Real, public, documented in [docs/DATA.md](docs/DATA.md):

- **GDV AKB 2015** — German Insurance Association model motor policy terms (RAG corpus)
- **Vehicle Insurance Fraud Detection** — 15,420 labelled real claims, CC0 (fraud model)
- **freMTPL2freq / freMTPL2sev** — 678k real French motor TPL policies, CC0 (realistic policyholder seed data)
- **InsuranceQA** — real consumer Q&A (RAG evaluation)

No real policy/claim data is linked across these sources publicly, so a thin seed layer joins them for the demo. That limitation is stated, not hidden.

## Repository layout

```
api/        FastAPI app (routers, SSE), LangGraph agent (api/agent), LLM providers (api/llm)
rag/        AKB chunking, embeddings, pgvector store, retriever, query rewriting, eval set
ml/         fraud-risk model: features, train, evaluate, explain, predict, model card, artifact
db/         SQLAlchemy models + Alembic migrations (policy chunks, conversations, checkpoints)
web/        Vue 3 single-page frontend, Vitest unit tests, Playwright e2e smoke
scripts/    fetch_data.py (AKB / OpenML / Kaggle), seed sampler, demo.sh
docs/       DECISIONS, DATA, ARCHITECTURE, ROADMAP, specs/, portfolio/, planning/
legacy/     archived v1 (not maintained)
```

## Running it

One command (needs [uv](https://docs.astral.sh/uv/) and Docker):

```bash
git clone https://github.com/parimalgavali/insureflow-ai && cd insureflow-ai
make demo        # fetches public data, ingests the AKB into pgvector, starts db + api + web
open http://localhost:8080
```

`scripts/demo.sh` uses recorded LLM replies by default so it works without any key; export
`ANTHROPIC_API_KEY` before running it for live Claude. With Kaggle credentials
(`KAGGLE_USERNAME`/`KAGGLE_KEY` or `~/.kaggle/kaggle.json`) it retrains the fraud model;
otherwise it uses the committed `ml/artifacts/fraud_model.joblib` (210 KB, reproducible via
`python -m ml.train`).

Development (local Postgres 16 + pgvector, `DATABASE_URL` defaults to `claimpilot/claimpilot@localhost`):

```bash
uv sync --all-extras && (cd web && npm install)
uv run python scripts/fetch_data.py all     # AKB PDF→text, freMTPL2, seed policyholders (+ Kaggle if creds)
uv run alembic upgrade head && uv run python -m rag.ingest
make dev                                    # API :8000 (recorded LLM) + Vite :5173
make test && make lint                      # 66 pytest + 8 vitest, ruff, vue-tsc
make e2e                                    # Playwright smoke: full conversation → adjuster review
uv run python -m rag.eval                   # retrieval eval, fails below 0.8 top-3
uv run python -m api.agent.demo             # live Anthropic run of the hit-and-run script
```

Demo auth: set `DEMO_API_TOKEN` in `.env` to require a bearer token (open when unset); uploads are
limited to JPEG/PNG/WebP/PDF ≤ `MAX_UPLOAD_MB` (10). `.env` is git-ignored; only `.env.example` is committed.

### Measured numbers

RAG over AKB 2015 — 28 hand-written DE/EN questions, hit if the expected clause is in the top 3
(`rag/eval/questions.jsonl`, run in CI):

| retrieval | top-1 | top-3 | DE top-3 | EN top-3 |
|---|---|---|---|---|
| multilingual-e5-small, dense only | 0.61 | 0.71 | 0.83 | 0.50 |
| + LLM query rewriting into German policy language | 0.61 | **0.89** | 0.89 | 0.90 |

Fraud-risk model — 15,420 real claims, 6% positive, held-out 20% (`ml/model_card.md`):

| model | AUPRC | ROC-AUC |
|---|---|---|
| majority class | 0.060 | 0.500 |
| logistic regression | 0.167 | 0.805 |
| HistGradientBoosting (`hgb-v1`) | **0.205** | **0.813** |

The model uses only features a conversation can supply and excludes protected attributes; it
ranks claims for adjuster attention and is never shown as a verdict.

Data cards with licenses and checksums: [`data/README.md`](data/README.md). Decisions and
measured alternatives: [`docs/DECISIONS.md`](docs/DECISIONS.md). Resume bullets and interview
Q&A: [`docs/portfolio/`](docs/portfolio/README.md).

## Why v2 exists

v1 (June–July 2026) was a wide Guidewire-style scaffold — 9 containers, 5 pages, 20 phases — on synthetic data, with "AI" components that were keyword matching and regexes. The audit and the reasoning for the reset are in [docs/planning/2026-10-27-v2-direction.md](docs/planning/2026-10-27-v2-direction.md) and [docs/DECISIONS.md](docs/DECISIONS.md). Narrow and real beats wide and shallow.

## Responsible AI

Outputs are decision support for a human reviewer. The fraud signal is a *risk score with reasons*, never a verdict. Coverage answers always cite the clause and say when evidence is missing. Everything runs on public data; nothing personal is stored beyond a demo conversation.

## License

MIT for the code. Data sources keep their own licenses (see docs/DATA.md).
