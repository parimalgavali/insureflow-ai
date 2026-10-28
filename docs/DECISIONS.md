# Decisions

Architecture Decision Records for InsureFlow AI v2. Newest at the bottom. One paragraph each; if it needs more, link a doc.

| # | Date | Decision | Why | Alternatives rejected |
| --- | --- | --- | --- | --- |
| 1 | 2026-10-27 | **Reset the project to v2 in place; archive v1 under `legacy/` with tag `v1-guidewire-prototype`.** | Keeps the 20-PR history as evidence of iteration and lets the README tell the "wide → narrow" story honestly. | New repo (loses history); keep extending v1 (its AI layer could not be made real without rewriting everything anyway). |
| 2 | 2026-10-27 | **One user-facing loop only: a policyholder files a motor claim by conversation.** | A single interactive screen is easier to make excellent, easier to demo in 2 minutes, and more relatable to any interviewer than an adjuster dashboard. | Adjuster copilot (more "industry", but a dashboard by nature); keep v1's five pages. |
| 3 | 2026-10-27 | **Python-only backend: FastAPI + LangGraph in one process.** | The agent, retriever, ML inference and API share types and tests; one container; the natural stack for AI-engineering roles. | Keep Spring Boot as API + Python AI service — doubles DTOs, tests and containers for a Java signal the user no longer prioritises. |
| 4 | 2026-10-27 | **Real public data instead of a synthetic generator.** Fraud model on Kaggle vehicle-fraud (CC0); RAG over GDV AKB 2015; freMTPL2 for policyholder seed rows. | v1's model learned back the rules that generated its labels. Real data gives honest metrics and real exclusions/deductibles to retrieve. | Keep/extend the synthetic generator; RISCBAC synthetic contracts (fine for NLP research, but synthetic again). |
| 5 | 2026-10-27 | **German policy corpus (AKB), bilingual DE/EN agent.** | The only public policy wording with clean clause numbering is German, and the user's job market is Germany. Multilingual embeddings (`intfloat/multilingual-e5-small` or similar) make DE↔EN retrieval work; the LLM answers in the user's language. | English-only with a UK insurer booklet (fine, but weaker local signal; booklet licensing less clear). |
| 6 | 2026-10-27 | **Anthropic Claude as primary LLM, Ollama as offline fallback, behind one provider interface.** | Quality for the demo; survivability when a key expires or in a network-restricted interview setting. | Single hard-wired provider; OpenAI (user has an Anthropic key). |
| 7 | 2026-10-27 | **pgvector in the same Postgres rather than a separate vector database.** | One database to run, migrate and back up; our corpus is tens of thousands of chunks at most. | Chroma/Qdrant/Weaviate — extra container, no benefit at this scale. |
| 8 | 2026-10-27 | **LangGraph for the agent; LangChain only for thin utilities (loaders, splitters, embeddings, structured output).** | A state graph with a conditional follow-up loop and an interrupt node is exactly what the conversation needs; it is readable in one file. | Hand-rolled loop (fine, but LangGraph's checkpointing and interrupts are the features we want to show); LangChain `AgentExecutor`-style chains (opaque). |
| 9 | 2026-10-27 | **Deep learning stays a stretch goal** (damage-photo tagger via a fine-tuned small CNN). Embedding models are already neural networks and are described as such, honestly. | Core loop first. A photo classifier is additive and must not block tasks 1–7. | Make it core (slows everything); claim "deep learning" without a trained network (dishonest). |
| 10 | 2026-10-27 | **Drop from v2:** RabbitMQ, Prometheus/Grafana, Azure Bicep, Guidewire-style integration APIs, governance dashboard, three AI microservices, JWT role matrix. | Each was infrastructure without a user-visible purpose in a one-screen product. | — |
| 11 | 2026-10-27 | **Work style: one task = one branch = one PR, with a one-page spec in `docs/specs/` before coding.** | Keeps reviews small and the roadmap honest. v1's 300-line phase plans were never re-read. | Big-bang rewrite. |
| 12 | 2026-10-27 | **Retrieval = dense `multilingual-e5-small` + LLM query rewrites into German policy language; no lexical/BM25 component.** | Measured on the 28-question eval set (`rag/eval`): e5-small dense-only 0.71 top-3 (DE 0.83, EN 0.50); e5-base 0.68; `paraphrase-multilingual-mpnet` 0.36; BM25 fused with dense (RRF, lexical weight 0.3–0.7) dropped to 0.43–0.54 because German compounds ("Wildunfall" vs "Zusammenstoß mit Haarwild") rarely share tokens. Query rewriting attacks exactly that gap and is recorded to a fixture so CI needs no API key. | Larger embedding models (`bge-m3`, `e5-large`: >2 GB, too slow on CPU for a laptop demo); hybrid BM25 (measured worse); hand-written synonym maps (the v1 anti-pattern). |

## 13. No damage-photo CNN (stretch item 1) — dataset provenance

**Decision:** skip the deep-learning photo tagger instead of training it on an image set whose rights are unclear.

**Why:** the spec required "a car-damage image set with an explicit license". Hugging Face has ~30 car-damage sets;
the ones with a permissive tag (`DrBimmer/comprehensive-car-damage` MIT, several `*/car-parts-and-damage-dataset` MIT
re-uploads, `Reverb/CarDamage` MIT) are uploader claims with `source_datasets: []`, no author, no origin — the photos
are almost certainly scraped or re-uploaded from Kaggle/Roboflow collections whose original terms are unknown. The large
one (`Naiscorp/car-damage-dataset`, 22k images) is `license: other` and unlabelled. A model card that says "trained on
images we may not have had the right to use" would undermine the honesty the rest of this repo is built on.

**What would unblock it:** an image set with a verifiable licence (e.g. the insurer's own photos, a CC-BY set with named
authors, or a synthetic set). The integration point is ready: `ClaimFacts.photos_attached` + the upload path in
`api/routers/conversations.py`; a tagger would add a `photo_tags` fact and a retrieval query per tag.

**Status of task 8:** items 2 (severity model, #39), 3 (DE/EN toggle, #40) and 4 (eval page, #41) are done; item 1 is
declined per this ADR; item 5 (more Musterbedingungen) stays open as a future idea.
