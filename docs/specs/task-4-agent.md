# Task 4 — LangGraph agent

**Goal:** the conversation brain: extract facts, ask for what is missing, retrieve coverage, score risk, compose a grounded answer, stop for human review. Runs offline in tests via recorded LLM responses.

**Deliverables (`api/agent/`)**
- `schemas.py`: `ClaimFacts` (incident date/time, location, what happened, parties, injuries, police report filed, witnesses, damage description, estimated amount, photos attached, vehicle facts from the seed policy), `RiskSignal`, `Citation`, `ClaimCard`, `AgentState`.
- `llm/provider.py`: `Provider.complete(messages, response_schema=None, stream=False)`; `AnthropicProvider` (structured output via tool/JSON schema), `OllamaProvider`, `RecordedProvider` (replays `tests/fixtures/*.json`; records when `RECORD=1`).
- `graph.py`: nodes `extract`, `check_missing`, `ask_followup`, `retrieve`, `score_risk`, `compose`, `human_review`; conditional edge on `missing`; `interrupt()` in `human_review`; `PostgresSaver` checkpointer keyed by conversation id.
- `prompts/`: versioned prompt files (`extract_v1.md`, `compose_v1.md`, `followup_v1.md`); compose prompt forbids coverage statements not present in retrieved chunks and requires `[A.2.3.2]`-style citations.
- `required_facts.py`: minimal set that must be known before coverage can be assessed (date, event type, third party involved?, damage description); follow-up questions ask for at most two at a time.
- Language handling: detect `de`/`en` from the user's first message; answer in that language; retrieval always queries the German corpus.

**Tests**
- Scripted conversation (hit-and-run on parked car) with recorded responses: asserts follow-up asked once, citations include an A.2.3 clause and an E.1 duty, risk band present, graph interrupts at `human_review`, resume completes.
- Grounding test: compose output with empty `retrieved` must state missing evidence and contain no clause ids.
- Provider contract tests for Anthropic/Ollama request shaping (no network).

**Done when:** `pytest api/agent` passes offline; `python -m api.agent.demo` runs the scripted conversation live with `ANTHROPIC_API_KEY`.

**Risks:** LangGraph API churn — pin versions; structured output failures — one retry with the validation error fed back, then graceful degradation to "could not extract, please rephrase".

**Secrets:** `ANTHROPIC_API_KEY` to record fixtures (once) and for live runs.
