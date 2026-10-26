# InsureFlow AI — Investigation & New Direction (Planning Doc, v0.1)

> Note: file paths cited in §1 refer to the v1 tree, which now lives under `legacy/` (tag `v1-guidewire-prototype`).

Date: 2026-10-27. Status: planning only, nothing in the repo changed yet.

---

## 1. What is in the repo today (honest audit)

Repo: https://github.com/parimalgavali/insureflow-ai — 20 merged PRs, 20 "phases", built June–July 2026 with Codex from a 3,600-line blueprint (`PROJECT_BLUEPRINT.md`). Target was Guidewire / Java insurance jobs in Germany.

| Layer | What exists | Size |
| --- | --- | --- |
| `backend/` | Java 21 Spring Boot 3.5: customers, policies, coverages, claims, FNOL, notes, documents, reserves, JWT roles, audit log, "Guidewire-inspired" `/integration/v1` APIs, governance endpoints, Flyway, Testcontainers | ~7,700 lines Java |
| `ai-services/` | 3 FastAPI microservices: triage, document-intelligence, rag | ~3,700 lines Python (incl. ml + generator) |
| `ml/` | scikit-learn RandomForest for severity + fraud labels | |
| `synthetic-data-generator/` | Generates customers/policies/claims CSVs + fake documents (motor only, EUR) | |
| `frontend/` | Vue 3 + Vite + TS, 5 nav pages (Claims, Documents, Governance, Integrations, Settings), 8 panels | ~3,100 lines |
| Infra | docker-compose with 9 services (Postgres, RabbitMQ, 3 AI services, API, frontend, Prometheus, Grafana), Azure Bicep, GitHub Actions, Trivy | |
| Docs | 16,700 lines of markdown (plans, specs, API docs, demo scripts, resume bullets) | |

### 1.1 What data does it use?

**100% synthetic, self-generated.** `data/sample/` and `data/synthetic/` contain only `.gitkeep`; the CSVs are produced locally by `synthetic-data-generator` from a random seed. No public or real dataset was ever wired in (the blueprint §12 *planned* to use the Kaggle vehicle-fraud dataset and RISCBAC contracts, but it never happened).

### 1.2 Is the "AI" actually AI?

No — this is the main problem for a portfolio. Everything is deterministic string matching dressed in AI vocabulary:

- **RAG service** (`ai-services/rag-service/rag_service/retrieval.py`): "retrieval" = count overlapping lowercase words between question and chunk, plus hand-coded bonuses (`if "coverage" in question_tokens: score += 0.15`). No embeddings, no vector store. **Answering** (`answering.py`) = three hard-coded template sentences chosen by `if "coverage" in top_text ... elif "police report" in top_text`. No LLM.
- **Document intelligence**: `DeterministicDocumentIntelligenceProvider` = regexes (`r"(\d{3,7})\s*(?:eur|euro|€)"`, `"rear bumper" in text`). The "prompt registry" and "retry on invalid JSON" wrap code that never calls a model.
- **ML triage**: a RandomForest trained on `ai_triage_labels.csv`, which the *same synthetic generator* produced from rules (`generator/rules.py`). The model learns back the rules that generated its labels — accuracy is meaningless and any interviewer who asks "where did the labels come from?" ends the conversation.
- No LangChain, LangGraph, embeddings, LLM API, or neural network anywhere in the codebase.

### 1.3 Verdict

Very wide, very shallow. It demonstrates enterprise scaffolding (lots of services, lots of docs) but the AI claims don't survive someone opening the code. For a 2026 portfolio aimed at AI + backend + frontend roles, the wiser move is **narrow and real**: one loop, real data, real models, one screen.

---

## 2. Proposed new direction: "ClaimPilot" — file a motor claim by conversation

One interactive screen. The user describes what happened in plain language (optionally drops a photo or invoice). An agent:

1. **Extracts** structured facts (date, what happened, third party, injuries, police report, estimated damage) — LLM with structured output.
2. **Asks follow-up questions** when something required is missing (LangGraph loop; this is what makes it feel interactive rather than a form).
3. **Checks coverage against the real policy wording** (RAG over the German GDV model motor insurance terms, AKB) and answers *with cited clauses*: "Glass damage is covered under Teilkasko, A.2.2.x — but your deductible is €150".
4. **Scores the claim** with a model trained on **real fraud data** (Kaggle vehicle-fraud, 15k claims) and shows the top reasons (feature contributions) — explicitly as decision support, not a decision.
5. Produces a **claim card**: structured claim, coverage verdict with sources, risk signal with reasons, missing documents list, and a "Send to adjuster" button (human-in-the-loop interrupt node).

That is the whole product. One page: chat on the left, the live-updating claim card on the right. No dashboards, no governance pages, no integrations page.

Why this works as a portfolio piece:
- **Backend engineering**: API design, persistence, streaming responses (SSE), background jobs for ingestion, auth, tests, Docker, CI.
- **Frontend engineering**: a small but polished chat UI with streaming tokens, citation popovers, file upload, optimistic state. Small surface = you can make it *really* good.
- **AI engineering**: RAG with real documents and evaluation, an actual LangGraph agent with tool calls and a human interrupt, a real ML model with honest metrics on an imbalanced dataset, and (stretch) a CNN on damage photos. Every buzzword backed by a file you can open.

### 2.1 Mapping the jargon to concrete, non-overcomplicated uses

| Term | Where it genuinely fits | How simple we keep it |
| --- | --- | --- |
| **RAG** | Policy-wording Q&A with citations | PDF → chunk by clause (AKB has numbered sections A.1.1…) → local embeddings (`sentence-transformers`, multilingual e5-small) → **pgvector in the same Postgres** (no extra vector DB) → top-k → LLM answer with clause refs. ~200 lines. |
| **LangChain** | Loaders, text splitter, embeddings wrapper, structured-output parsing | Use the thin pieces only; don't build on `AgentExecutor`/chains. |
| **LangGraph** | The conversation agent as a state graph: `extract → check_missing → (ask | continue) → retrieve_coverage → score_risk → compose_card → human_review (interrupt)` | 6–7 nodes, one conditional edge, Postgres checkpointer so conversations resume. This is the heart of the AI story. |
| **Machine learning** | Fraud-risk model on real labelled claims | `scikit-learn` HistGradientBoosting, stratified CV, AUPRC/recall at fixed precision (imbalanced!), feature contributions for explanations, saved artifact + model card. One training script, one notebook. |
| **Deep learning / neural networks** | (a) the embedding model *is* a transformer — say so honestly; (b) stretch: damage-photo classifier | Stretch only: fine-tune a small pretrained CNN (e.g. ResNet-18 / MobileNet via torchvision) on a public car-damage image set to tag damage type; feed the tag into the agent. Cut if time is short. |
| **LLM** | Extraction, follow-up question wording, grounded answer | Provider-agnostic: OpenAI/Anthropic for quality, **Ollama** (e.g. a small local model) for offline demo so the project never dies when a key expires. |

Things we deliberately do **not** do: fine-tune an LLM, multi-agent swarms, Kubernetes, RabbitMQ, Prometheus/Grafana, Guidewire integration facades, governance registries.

---

## 3. Real data — verified today (2026-10-27)

| # | Dataset | What it is | Access / license | Use |
| --- | --- | --- | --- | --- |
| 1 | **Vehicle Insurance Fraud Detection** (Kaggle `khusheekapoor/vehicle-insurance-fraud-detection`, a.k.a. `carclaims` / `fraud_oracle.csv`) | 15,420 real US auto claims 1994–96, 923 fraud (6%), 33 columns: Make, AccidentArea, Fault, PolicyType, VehicleCategory, Deductible, PastNumberOfClaims, PoliceReportFiled, WitnessPresent, AgeOfVehicle, Days_Policy_Claim… | CC0. **Needs a Kaggle account/API token to download** (page confirmed live). | Fraud-risk ML model. Honest imbalanced classification. |
| 2 | **freMTPL2freq + freMTPL2sev** (OpenML 41214 / 41215, from CASdatasets) | 677,991 real French motor third-party-liability policies (Exposure, Area, VehPower, VehAge, DrivAge, BonusMalus, VehBrand, VehGas, Density, Region, ClaimNb) + 26,639 claim amounts | CC0, **downloadable with no login** via OpenML API. | Severity/frequency model, or realistic policyholder seed data (ages, vehicles, bonus-malus) instead of our fake generator. |
| 3 | **GDV Musterbedingungen — AKB 2015** (German Insurance Association model motor terms) | 55 pages, ~21k words, real industry policy wording; numbered clauses (A.1 Haftpflicht, A.2 Kasko, D Pflichten, E Schadenfall…). Text extracts cleanly with `pypdf` (tested). 77 more GDV PDFs on the same page (household, liability, legal). | Public on gdv.de (check reuse terms before redistributing; link + download script rather than committing the PDF). | **The RAG corpus.** Real clauses, real exclusions, real deductible logic. |
| 4 | **InsuranceQA** (GitHub `shuzi/insuranceQA`, 467★; HF `deccan-ai/insuranceQA-v2`, 10k–100k rows) | Real consumer insurance questions + licensed-agent answers from insurancelibrary.com (English). | Research dataset (ASRU 2015 paper); license not stated on HF. | RAG **evaluation** set / general insurance FAQ fallback corpus. |
| 5 | **Car damage image sets** on Hugging Face (e.g. `DrBimmer/comprehensive-car-damage`, `riddhi114/car-damage-dataset-with-yolov8`, `gigwegbe/damaged-car-dataset-annotated`) | Labelled photos of dents/scratches/broken glass | Licenses mostly unstated — pick one with a clear license before training. | Stretch: deep-learning damage tagger. |
| – | Kaggle `buntyshah/auto-insurance-claims-data` (1,000 rows) | Looks synthetic, tiny | – | Skip. |

Gap to be aware of: there is no public dataset that links *claim text → policy → fraud label*. Real text + real tabular + real policy wording will come from three sources, joined by our own thin seed layer (a few demo policyholders). That is normal and defensible; say it in the README.

**Language question:** the only real policy wording with clean clause structure is German (AKB). Options: (a) German corpus, bilingual agent (LLM answers in the user's language, multilingual embeddings handle DE↔EN retrieval) — most authentic for a Germany job search; (b) find an English insurer's public policy booklet (e.g. a UK motor policy PDF) and go English-only. Recommendation: (a).

---

## 4. Minimal target architecture

```
Browser (one page: chat + claim card)
   │  HTTP + SSE
   ▼
FastAPI app  ───────────────  Postgres (+ pgvector extension)
   ├─ /conversations, /messages (SSE stream)     ├─ conversations, messages, claims
   ├─ /claims/{id}, /claims/{id}/review          ├─ policy_chunks (embeddings)
   ├─ LangGraph agent (in-process)               └─ langgraph checkpoints
   │    nodes: extract → check_missing → retrieve → score → compose → human_review
   ├─ ML artifact (fraud model .joblib + explainer)
   └─ LLM provider (OpenAI/Anthropic | Ollama)
```

Three containers in `docker compose up`: `db`, `api`, `web`. One language for the backend, one for the frontend.

**Backend language decision (needs your call):**
- **Option A — Python only (FastAPI)**: agent, RAG, ML and API live in one process. Simplest, fastest, and the natural stack for AI-engineer roles. The Java code goes to the `v1` tag.
- **Option B — keep Spring Boot as the API + Python as the AI service**: shows Java, but doubles every feature (DTOs twice, two test suites, two containers) — exactly the complexity you said you want to avoid. Only worth it if Java/Guidewire roles are still the primary target.

Frontend: keep **Vue 3 + Vite + TS** (already set up, fine for a chat UI) — or switch to React if that's what target jobs list more. Either is a one-page build.

---

## 5. What happens to the existing code

Recommendation: **reset in place, don't start a new repo.** Tag the current `main` as `v1-guidewire-prototype`, move it under `legacy/` for one release (or delete it — the tag keeps it), rewrite the README with the new pitch. This keeps the 20-PR history as evidence of iteration and lets the README say "v1 was broad scaffolding; v2 narrows to one real AI loop" — that story itself is a good interview answer.

Keep: Vue/Vite setup, Postgres + Flyway idea (as Alembic in Python), GitHub Actions skeleton, Dockerfiles pattern, the Responsible-AI stance (decision support, human review).
Drop: Spring Boot (if Option A), RabbitMQ, Prometheus/Grafana, Azure Bicep, 3 microservices, integration APIs, governance pages, synthetic generator (replace with a small seed script over freMTPL rows), 16k lines of phase docs (archive).

---

## 6. Task breakdown (each = one branch/PR, roughly in order)

| # | Task | Done when |
| --- | --- | --- |
| 0 | **Repo reset & docs** — tag v1, archive, new README (pitch, architecture, data sources, honesty notes), `docs/DECISIONS.md` | README tells the new story; CI green on an almost-empty tree |
| 1 | **Data layer** — `data/README.md` with sources + licenses; `scripts/fetch_data.py` (OpenML direct, GDV PDFs direct, Kaggle via `kaggle` CLI with token); data cards | One command fetches everything given a Kaggle token; nothing large committed |
| 2 | **Fraud model** — EDA notebook, `ml/train.py` (HistGradientBoosting, stratified CV, AUPRC, calibration), feature contributions, `model_card.md`, saved artifact, tests | Metrics table in model card; `predict(claim_features) → {score, top_reasons}` |
| 3 | **RAG over AKB** — clause-aware chunking, embeddings, pgvector table, `retrieve(question) → chunks`, 25 hand-written DE/EN eval questions with expected clause ids, hit-rate report | ≥80% top-3 hit rate on the eval set; answers carry clause citations |
| 4 | **LangGraph agent** — state schema, nodes, conditional follow-up loop, Postgres checkpointer, human-review interrupt, LLM provider abstraction (API + Ollama), recorded-response tests | Scripted conversation test passes offline with recorded LLM outputs |
| 5 | **Backend API** — FastAPI, SQLAlchemy/Alembic, SSE streaming endpoint, file upload, minimal auth (single demo user / magic token), OpenAPI | `docker compose up` → curl a full conversation |
| 6 | **Frontend** — one-page chat + claim card, token streaming, citation popovers, follow-up prompts as chips, upload, review button, mobile-friendly | Demo flow runs end to end in < 2 minutes |
| 7 | **Quality & release** — pytest + vitest + Playwright smoke in CI, 60-second demo GIF, final README, resume bullets | Public repo a recruiter can run with one command |
| 8 | **Stretch (optional)** — damage-photo CNN tagger feeding the agent; freMTPL severity model; German/English UI toggle; small RAG-eval page | Only after 0–7 are solid |

Estimated effort: tasks 0–7 ≈ 4–6 focused sessions. Each task gets its own short spec before coding, as before — but 1 page, not 300 lines.

---

## 7. Decisions needed from you before task 0

1. **Backend**: Python-only (A, recommended) or Spring Boot + Python (B)?
2. **Persona**: policyholder filing a claim (recommended — more relatable, simpler) or adjuster copilot reviewing claims?
3. **Language**: German policy corpus with bilingual agent (recommended) or English-only?
4. **LLM access**: do you have / want an OpenAI or Anthropic API key, or Ollama-only?
5. **Kaggle**: can you create a Kaggle API token (needed for dataset #1)?
6. **Repo**: reset in place with `v1` tag (recommended) or brand-new repo?
