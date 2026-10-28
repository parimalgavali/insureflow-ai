# Roadmap

One task = one branch = one PR = one one-page spec in `docs/specs/`. A task is done when its "Done when" column is true and the PR is merged. Order matters: 0 → 7; 8 only after 7.

| # | Task | Spec | Done when | Status |
| --- | --- | --- | --- | --- |
| 0 | Repo reset & docs | [task-0](specs/task-0-repo-reset.md) | `v1-guidewire-prototype` tag exists; v1 under `legacy/`; README/DECISIONS/DATA/ARCHITECTURE/ROADMAP/specs merged | done — [PR #21](https://github.com/parimalgavali/insureflow-ai/pull/21) |
| 1 | Data layer | [task-1](specs/task-1-data-layer.md) | `python scripts/fetch_data.py` downloads AKB + OpenML; with a Kaggle token also the fraud CSV; `data/eval/` seeded; data cards written | in review — [#22](https://github.com/parimalgavali/insureflow-ai/issues/22), branch `task-1-data-layer` |
| 2 | Fraud-risk model | [task-2](specs/task-2-fraud-model.md) | `ml/train.py` produces artifact + `model_card.md` with AUPRC/recall@precision; `predict()` returns score + 3 reasons; tests green | todo — [#23](https://github.com/parimalgavali/insureflow-ai/issues/23) |
| 3 | RAG over AKB | [task-3](specs/task-3-rag-akb.md) | clause-aware ingestion into pgvector; ≥ 0.8 top-3 hit rate on 25 hand-written DE/EN questions; retriever returns clause ids | in review — [#24](https://github.com/parimalgavali/insureflow-ai/issues/24), branch `task-3-rag-akb` |
| 4 | LangGraph agent | [task-4](specs/task-4-agent.md) | graph with follow-up loop + human interrupt; Postgres checkpointer; provider abstraction (Anthropic/Ollama); scripted conversation test passes offline with recorded responses | in review — [#25](https://github.com/parimalgavali/insureflow-ai/issues/25), branch `task-4-agent` |
| 5 | Backend API | [task-5](specs/task-5-api.md) | FastAPI + Alembic; SSE message endpoint; `docker compose up` → full conversation via curl; CI green | in review — [#26](https://github.com/parimalgavali/insureflow-ai/issues/26), branch `task-5-api` |
| 6 | Frontend | [task-6](specs/task-6-frontend.md) | one-page chat + claim card with streaming, citations, chips, upload, review button; demo flow < 2 min | todo — [#27](https://github.com/parimalgavali/insureflow-ai/issues/27) |
| 7 | Quality & release | [task-7](specs/task-7-quality-release.md) | Playwright smoke in CI; 60-s demo GIF in README; resume bullets; a stranger can run it with one command | todo — [#28](https://github.com/parimalgavali/insureflow-ai/issues/28) |
| 8 | Stretch | [task-8](specs/task-8-stretch.md) | damage-photo CNN tagger; freMTPL severity model; DE/EN UI toggle; small RAG-eval page | later — [#29](https://github.com/parimalgavali/insureflow-ai/issues/29) |

Rough effort: tasks 0–7 ≈ 4–6 focused sessions.

Each task has a GitHub issue (user story + acceptance criteria), a feature branch named `task-N-<slug>` and one PR that closes the issue.

## Secrets needed and when

| Secret | First needed | Purpose |
| --- | --- | --- |
| Kaggle API token (`kaggle.json`) | task 1 | download `fraud_oracle.csv` |
| `ANTHROPIC_API_KEY` | task 4 (recording fixtures), task 5+ at runtime | LLM provider |

## Out of scope for v2

Multi-user auth, payments, adjuster dashboards, integrations with core systems, metrics stacks, cloud IaC. See `DECISIONS.md` #10.
