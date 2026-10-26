# Task 3 — RAG over AKB 2015

**Goal:** retrieve the right AKB clauses for a claim question in German or English, with clause ids, measured against a hand-written evaluation set.

**Deliverables (`rag/`)**
- `chunking.py`: split `akb_2015.txt` on clause numbering (`^[A-Z]\.\d+(\.\d+)*`) → `Chunk(clause_id, title, text, parent_id, page)`; merge sub-clauses under ~800 tokens; keep heading chain for context.
- `embeddings.py`: multilingual sentence-transformer (small, CPU; candidate `intfloat/multilingual-e5-small`), batched, cached.
- `ingest.py`: writes chunks + vectors to Postgres `policy_chunks` (pgvector, HNSW index); idempotent by content hash.
- `retriever.py`: `retrieve(query: str, k=5, lang="de"|"en") -> list[ScoredChunk]`; builds German query variants from English input via a short prompt (or relies on multilingual embeddings — measure both).
- `eval/questions.jsonl`: 25 questions (≈15 DE, 10 EN) with expected clause ids, covering Haftpflicht vs Teilkasko vs Vollkasko, hit-and-run, glass, theft, wild animal, deductible, duties after a loss (E.*), police report, late reporting consequences, gross negligence.
- `eval.py`: top-1/top-3 hit rate, MRR; prints a table; fails CI if top-3 < 0.8.
- Alembic migration for `policy_chunks` (lands here, used by task 5).

**Tests:** chunker on a fixture page (clause ids and parents correct); retriever against a tiny in-memory corpus; eval runs end-to-end in CI against a Postgres service container.

**Done when:** `python -m rag.ingest && python -m rag.eval` reports ≥ 0.8 top-3; retriever returns clause ids usable as citations.

**Risks:** PDF text has hyphenation/line-break noise — normalise before chunking; e5 models expect `query:`/`passage:` prefixes — follow the model card.
