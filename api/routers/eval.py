"""Dev-only retrieval evaluation page data: the 28 DE/EN questions, what was retrieved, hit/miss.

Enabled with EVAL_PAGE=1 (default on when LLM_PROVIDER=recorded, i.e. local/demo runs; off in the
public Space) and behind the demo token. Results are computed once per process and allowed `k`
against the live retriever and cached — the same code path as `python -m rag.eval`, just served as
JSON so the UI can show that the retriever is measured.
"""

from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.security import get_state, require_token

K_MIN, K_MAX = 3, 10

router = APIRouter(prefix="/api", tags=["eval"], dependencies=[Depends(require_token)])


@lru_cache(maxsize=K_MAX - K_MIN + 1)
def _run(state_id: int, retriever: Any, k: int) -> dict:
    from rag.eval import THRESHOLD, evaluate, load_questions, summarise

    results = evaluate(retriever, load_questions(), k=k)
    summary = summarise(results)
    return {
        "k": k,
        "threshold": THRESHOLD,
        "summary": summary,
        "passed": summary["top3"] >= THRESHOLD,
        "results": [
            {
                **asdict(r.question),
                "retrieved": r.retrieved,
                "rank": r.rank,
                "hit": r.rank is not None and r.rank <= 3,
            }
            for r in results
        ],
    }


@router.get("/eval")
def retrieval_eval(k: int = 5, state=Depends(get_state)) -> dict:
    if not state.settings.eval_page:
        raise HTTPException(404, "eval page disabled (set EVAL_PAGE=1)")
    if state.retriever is None:
        raise HTTPException(503, "retriever unavailable")
    return _run(id(state), state.retriever, min(max(k, K_MIN), K_MAX))
