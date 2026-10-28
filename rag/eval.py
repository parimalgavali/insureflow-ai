"""Retrieval evaluation against hand-written DE/EN questions with expected AKB clause ids.

    uv run python -m rag.eval                        # Postgres (after rag.ingest)
    uv run python -m rag.eval --memory               # chunk + embed in-process, no database needed
    uv run python -m rag.eval --rewriter none        # dense retrieval only
    uv run python -m rag.eval --record               # refresh eval/rewrites.json with Anthropic

Exit code 1 when top-3 hit rate < THRESHOLD, so CI fails on retrieval regressions.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from rag.retriever import Retriever
from rag.store import ScoredChunk

QUESTIONS_PATH = Path(__file__).parent / "eval" / "questions.jsonl"
THRESHOLD = 0.8


@dataclass
class Question:
    id: str
    lang: str
    question: str
    expected: list[str]
    topic: str = ""


@dataclass
class EvalResult:
    question: Question
    retrieved: list[str]
    rank: int | None  # 1-based rank of the first hit, None if no hit in top-k


def load_questions(path: Path = QUESTIONS_PATH) -> list[Question]:
    questions = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            data = json.loads(line)
            questions.append(Question(**data))
    return questions


def is_hit(retrieved_id: str, expected: list[str]) -> bool:
    """Hit if the chunk *is* an expected clause or sits beneath one (A.2.2.2.2 for A.2.2.2)."""
    return any(retrieved_id == e or retrieved_id.startswith(e + ".") for e in expected)


def first_hit_rank(hits: list[ScoredChunk], expected: list[str]) -> int | None:
    seen: list[str] = []
    for hit in hits:
        cid = hit.chunk.clause_id
        if cid in seen:
            continue
        seen.append(cid)
        if is_hit(cid, expected):
            return len(seen)
    return None


def evaluate(retriever: Retriever, questions: list[Question], k: int = 5) -> list[EvalResult]:
    results = []
    for q in questions:
        hits = retriever.retrieve(q.question, k=k, lang=q.lang)  # type: ignore[arg-type]
        results.append(
            EvalResult(q, [h.chunk.clause_id for h in hits], first_hit_rank(hits, q.expected))
        )
    return results


def summarise(results: list[EvalResult]) -> dict[str, float]:
    def rate(subset: list[EvalResult], n: int) -> float:
        return (
            sum(1 for r in subset if r.rank is not None and r.rank <= n) / len(subset)
            if subset
            else 0.0
        )

    def mrr(subset: list[EvalResult]) -> float:
        return sum(1 / r.rank for r in subset if r.rank) / len(subset) if subset else 0.0

    out = {
        "n": len(results),
        "top1": rate(results, 1),
        "top3": rate(results, 3),
        "mrr": mrr(results),
    }
    for lang in ("de", "en"):
        subset = [r for r in results if r.question.lang == lang]
        out[f"top3_{lang}"] = rate(subset, 3)
        out[f"n_{lang}"] = len(subset)
    return out


def print_report(results: list[EvalResult], summary: dict[str, float]) -> None:
    print(f"{'id':<6}{'lang':<5}{'rank':<6}{'expected':<22}retrieved (top-5)")
    for r in results:
        rank = str(r.rank) if r.rank else "-"
        expected = ",".join(r.question.expected)
        print(
            f"{r.question.id:<6}{r.question.lang:<5}{rank:<6}{expected:<22}{', '.join(r.retrieved)}"
        )
    print()
    s = summary
    print(
        f"n={s['n']}  top-1={s['top1']:.2f}  top-3={s['top3']:.2f}  MRR={s['mrr']:.2f}  "
        f"| DE top-3={s['top3_de']:.2f} (n={s['n_de']})  "
        f"EN top-3={s['top3_en']:.2f} (n={s['n_en']})"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--memory", action="store_true", help="build an in-memory index instead of using Postgres"
    )
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--questions", type=Path, default=QUESTIONS_PATH)
    parser.add_argument(
        "--json", type=Path, help="write summary + per-question results to this file"
    )
    parser.add_argument("--rewriter", choices=["none", "recorded", "anthropic"], default="recorded")
    parser.add_argument(
        "--record", action="store_true", help="call Anthropic and save rewrites.json"
    )
    args = parser.parse_args(argv)

    from rag.embeddings import Embedder

    embedder = Embedder()
    if args.memory:
        from rag.chunking import chunk_akb
        from rag.ingest import ingest
        from rag.store import InMemoryStore

        store = InMemoryStore()
        ingest(chunk_akb(), store, embedder)
    else:
        from rag.store import PgVectorStore

        store = PgVectorStore()
        if store.count() == 0:
            print(
                "error: policy_chunks is empty; run `python -m rag.ingest` first", file=sys.stderr
            )
            return 1

    questions = load_questions(args.questions)
    if args.record:
        from rag.query_rewrite import AnthropicRewriter, RecordedRewriter

        live, recorded = AnthropicRewriter(), RecordedRewriter()
        for q in questions:
            recorded.record(q.question, live.rewrite(q.question, q.lang))
        recorded.save()
        print(f"recorded rewrites for {len(questions)} questions -> {recorded.path}")

    from rag.query_rewrite import make_rewriter

    dense_only = summarise(evaluate(Retriever(store, embedder), questions, k=args.k))
    results = evaluate(
        Retriever(store, embedder, make_rewriter(args.rewriter)), questions, k=args.k
    )
    summary = summarise(results)
    print_report(results, summary)
    print(
        f"dense only: top-1={dense_only['top1']:.2f} top-3={dense_only['top3']:.2f} "
        f"DE={dense_only['top3_de']:.2f} EN={dense_only['top3_en']:.2f}"
    )
    summary["dense_only_top3"] = dense_only["top3"]
    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "summary": summary,
                    "results": [
                        {
                            "id": r.question.id,
                            "lang": r.question.lang,
                            "rank": r.rank,
                            "retrieved": r.retrieved,
                        }
                        for r in results
                    ],
                },
                indent=2,
            )
        )
    if summary["top3"] < THRESHOLD:
        print(f"FAIL: top-3 hit rate {summary['top3']:.2f} < {THRESHOLD}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
