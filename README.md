# InsureFlow AI — ClaimPilot

**File a motor insurance claim by talking to it.** One screen: a chat on the left, a live claim card on the right. An agent extracts the facts, asks for what is missing, checks coverage against the *real* policy wording with clause citations, scores fraud risk with a model trained on *real* claims, and hands the result to a human reviewer.

> Portfolio project by Parimal Gavali. Backend engineering + frontend engineering + applied AI, each backed by something you can open and read. Decision support only — nothing here approves, denies or accuses.

**Status:** v2 in progress. The v1 prototype is archived under [`legacy/`](legacy/README.md) (tag `v1-guidewire-prototype`). Current step: see [docs/ROADMAP.md](docs/ROADMAP.md).

---

## What it does (target for v2)

```
You:   Someone hit my parked car last night in Bielefeld, rear bumper is cracked.
       They drove off. I have photos.
Agent: Sorry to hear that. Two quick questions: do you know the date, and did
       you report it to the police?
You:   Yesterday, 26 Oct. Not yet.
Agent: Thanks. Here is where you stand:
       • Coverage: a hit-and-run on a parked car is a Vollkasko event (AKB A.2.3.2);
         Teilkasko alone would not cover it (A.2.2). Your deductible is €300.
       • Missing: police report — required for hit-and-run (AKB E.1.1.3). I've added it
         to your to-do list.
       • Risk signal: low. Reasons: no prior claims, report filed within 1 day,
         damage amount consistent with description.
       Ready to send this to an adjuster?
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

## Repository layout (v2)

```
api/        FastAPI app, agent, retriever, ML inference         (task 4–5)
ml/         training script, evaluation, model card             (task 2)
rag/        ingestion, chunking, eval questions                 (task 3)
web/        Vue 3 single-page frontend                          (task 6)
scripts/    fetch_data.py and friends                           (task 1)
docs/       DECISIONS, DATA, ARCHITECTURE, ROADMAP, specs/, planning/
legacy/     archived v1 (not maintained)
```

## Running it

Not yet — v2 is being rebuilt task by task. Each task ends with a PR and a short spec in [docs/specs/](docs/specs/). When task 5 lands, `docker compose up` will bring up the API; task 6 adds the UI.

## Why v2 exists

v1 (June–July 2026) was a wide Guidewire-style scaffold — 9 containers, 5 pages, 20 phases — on synthetic data, with "AI" components that were keyword matching and regexes. The audit and the reasoning for the reset are in [docs/planning/2026-10-27-v2-direction.md](docs/planning/2026-10-27-v2-direction.md) and [docs/DECISIONS.md](docs/DECISIONS.md). Narrow and real beats wide and shallow.

## Responsible AI

Outputs are decision support for a human reviewer. The fraud signal is a *risk score with reasons*, never a verdict. Coverage answers always cite the clause and say when evidence is missing. Everything runs on public data; nothing personal is stored beyond a demo conversation.

## License

MIT for the code. Data sources keep their own licenses (see docs/DATA.md).
