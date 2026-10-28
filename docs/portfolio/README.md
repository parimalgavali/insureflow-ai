# Portfolio material

Short, honest texts for presenting ClaimPilot. Numbers come from `ml/model_card.md` and `rag/eval`.

## Resume bullets

- Built **ClaimPilot**, a conversational motor-claim intake agent (FastAPI + LangGraph + Vue 3) that turns a free-text accident description into a structured claim with cited policy clauses and a human-review gate.
- Implemented **RAG over real German policy wording** (GDV AKB 2015): clause-aware chunking into 344 citable units, multilingual e5 embeddings in **pgvector**, LLM query rewriting — raised DE/EN top-3 retrieval from 0.71 to 0.89 on a 28-question eval that gates CI.
- Designed a **LangGraph** state graph with a follow-up loop, grounding enforcement (uncited clause ids are stripped), `interrupt()`-based human-in-the-loop review and Postgres checkpointing; provider abstraction for Anthropic, Ollama and recorded fixtures so the full suite runs offline.
- Trained an **explainable fraud-risk model** (scikit-learn HistGradientBoosting) on 15,420 real claims with protected attributes excluded; AUPRC 0.205 vs 0.167 logistic baseline, documented in a model card as decision support only.
- Shipped **streaming SSE API**, single-page Vue UI with live claim card, Playwright e2e smoke, Docker Compose and a one-command demo; CI runs lint, unit, RAG eval, e2e and image builds.

## Interview Q&A

**1. Why a conversation instead of a form?**
The hard part of claim intake is that people describe events in their own words and leave facts out. The agent extracts what it can into a typed schema (`ClaimFacts`), checks a required-facts list and asks only for what is missing (max 3 follow-ups). The live claim card makes the extraction transparent, so the user corrects the model instead of trusting it blindly.

**2. Where does LangGraph add value over a plain function chain?**
Three places: the conditional loop (`check_missing → ask_followup` vs `→ retrieve`), the `interrupt()` before human review with state persisted in Postgres so the conversation can resume hours later, and the fact that every node is unit-testable with injected dependencies (`AgentDeps`).

**3. How do you stop the model inventing policy clauses?**
Compose receives only the retrieved chunks; afterwards `_enforce_citations` removes any `[X.Y.Z]` not in the retrieved set and appends a note. If retrieval returns nothing, the answer is a fixed "no evidence" text with zero citations. The e2e fixture deliberately includes a bogus `[Z.9.9]` to prove the path.

**4. Why did dense retrieval alone miss English questions, and what fixed it?**
The corpus is German legal text; English paraphrases ("hit-and-run", "deductible") land far from "Unfallflucht"/"Selbstbeteiligung" even for a multilingual embedder (EN top-3 = 0.50). Rewriting each query into up to three German policy-language variants raised EN top-3 to 0.90. BM25 hybrid and larger embedders were measured and were worse (ADR 12).

**5. The fraud model's AUPRC is 0.2 — is that good?**
Base rate is 6%, so 0.2 is 3.4× random and beats logistic regression, but recall at precision ≥ 0.5 is only 2%. I deliberately dropped the dataset's strongest predictor (`AddressChange-Claim`) because a conversation cannot observe it; using it would have inflated offline metrics with a feature that is constant at inference. The model ranks claims for adjuster attention; it does not classify.

**6. What did you exclude for fairness and how is that enforced?**
`Sex`, `MaritalStatus`, `Age`, `AgeOfPolicyHolder` plus the identifiers never enter the feature list; a test asserts `EXCLUDED ∩ FEATURES = ∅` and the training function raises otherwise. The model card states the exclusions and the limitation that proxies may remain.

**7. How are the explanations computed, and what are their limits?**
Per prediction, each feature is swapped for its training baseline and the probability drop recorded; the top three with a drop ≥ 0.005 are phrased from a template map. It is a local sensitivity, not Shapley values and not causal — the card says so, and features whose only "signal" was calendar noise were removed because they produced embarrassing reasons.

**8. How do you test an LLM application deterministically?**
A `RecordedProvider` replays per-node responses from a JSON fixture; retrieval in tests uses a deterministic bag-of-words embedder over a committed AKB excerpt; the Playwright smoke test runs the real API + Postgres with the recorded provider. Live Anthropic runs are manual (`python -m api.agent.demo`) and used to refresh fixtures.

**9. What would break in production?**
Concurrency: one recorded-fixture process per conversation is a demo shortcut; the Anthropic path is fine but needs rate-limit handling and retries. Security: single shared bearer token, no per-user auth, uploads stored on local disk. Data: a 1990s US fraud dataset does not transfer to German claims — the model would need retraining on the insurer's own data, with monitoring for drift and disparate impact. Retrieval: 344 chunks fit in one table; many policy versions need metadata filtering by product/version. Observability: no tracing of prompts/latency yet.

**10. What would you do next with one more week?**
Streaming tokens from the compose step (currently word-grouped after structured output), policy-version filtering in retrieval, a `teilkasko`-specific retrieval query set, a small labelled set of real German claim descriptions to measure extraction accuracy, and a CNN damage-photo classifier only if a clearly licensed image dataset is available.

## LinkedIn post

I rebuilt my insurance side project from a wide, synthetic "platform" into one thing that works end to end: ClaimPilot, a chat that files a motor claim. You describe what happened, a LangGraph agent asks what is missing, cites the actual GDV AKB 2015 policy wording (RAG over 344 clauses in pgvector, DE/EN), attaches an explainable fraud-risk signal from a model trained on 15,420 real claims, and then stops — a human adjuster reviews before anything moves. Every number in the README is measured and reproducible in CI, including the ones that are modest. Code, model card and decision log are public.
