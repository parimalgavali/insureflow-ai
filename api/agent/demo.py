"""Run the scripted hit-and-run conversation live.

LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=... uv run python -m api.agent.demo
uv run python -m api.agent.demo --recorded   # replay tests/fixtures/agent/hit_and_run.json
RECORD=1 uv run python -m api.agent.demo     # re-record that fixture with the live provider
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver

from api.agent.graph import AgentDeps, build_graph, pending_interrupt, resume_review, run_turn
from api.agent.schemas import PolicyContext, ReviewDecision
from api.llm.provider import RecordedProvider, make_provider

FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "agent" / "hit_and_run.json"
SCRIPT = [
    "Gestern Abend hat jemand mein geparktes Auto auf dem Supermarktparkplatz in Köln "
    "angefahren und ist einfach weggefahren. Die hintere Stoßstange ist eingedrückt.",
    "Das war am 25.10.2026 gegen 19 Uhr. Die Polizei habe ich nicht gerufen, Zeugen gab es keine.",
]


def build_retriever():
    try:
        from rag.embeddings import Embedder
        from rag.query_rewrite import RecordedRewriter
        from rag.retriever import Retriever
        from rag.store import PgVectorStore

        store = PgVectorStore()
        if store.count() == 0:
            raise RuntimeError("policy_chunks is empty; run `python -m rag.ingest`")
        return Retriever(store, Embedder(), RecordedRewriter())
    except Exception as exc:  # noqa: BLE001 - demo should still run without Postgres
        print(f"[demo] retrieval disabled: {exc}", file=sys.stderr)
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--recorded", action="store_true", help="replay the test fixture instead of calling an LLM"
    )
    parser.add_argument("--today", default="2026-10-26")
    args = parser.parse_args(argv)

    if args.recorded:
        provider = RecordedProvider(FIXTURE)
    elif os.environ.get("RECORD") == "1":
        provider = RecordedProvider(FIXTURE, record_from=make_provider())
    else:
        provider = make_provider()
    deps = AgentDeps(
        provider=provider,
        retriever=None if args.recorded else build_retriever(),
        today=lambda: args.today,
    )
    graph = build_graph(deps, checkpointer=MemorySaver())
    thread = "demo"
    policy = PolicyContext(product="vollkasko", deductible_eur=300)

    for text in SCRIPT:
        print(f"\nUSER: {text}")
        result = run_turn(graph, thread, text, policy)
        print(f"AGENT: {result['messages'][-1].content}")
        if pending_interrupt(result):
            break
    card = result.get("card")
    if card:
        print("\nCLAIM CARD:", card.model_dump_json(indent=2, exclude={"coverage_summary"}))
        result = resume_review(graph, thread, ReviewDecision(decision="accept", note="looks fine"))
        print(f"\nREVIEW → status={result['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
