"""Retrieve AKB clauses for a question; returns scored chunks whose clause ids are citations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from rag.embeddings import EmbedderProtocol
from rag.query_rewrite import NoRewriter, QueryRewriter
from rag.store import ScoredChunk, VectorStore

Lang = Literal["de", "en"]


class Retriever:
    """Dense retrieval over policy chunks, optionally widened by LLM query rewrites.

    The multilingual embedding model handles German questions well on its own; English questions
    and colloquial phrasing ("zerkratzt" vs. the wording's "böswillige Handlungen") benefit from
    the rewriter, which adds German policy-language variants of the question. Results from all
    variants are merged and ranked by best cosine score."""

    def __init__(
        self,
        store: VectorStore,
        embedder: EmbedderProtocol,
        rewriter: QueryRewriter | None = None,
    ):
        self.store = store
        self.embedder = embedder
        self.rewriter = rewriter or NoRewriter()

    def retrieve(self, query: str, k: int = 5, lang: Lang = "de") -> list[ScoredChunk]:
        queries = [query]
        for variant in self.rewriter.rewrite(query, lang):
            if variant.strip() and variant.strip() not in queries:
                queries.append(variant.strip())
        return self.retrieve_many(queries, k=k)

    def retrieve_many(self, queries: Sequence[str], k: int = 5) -> list[ScoredChunk]:
        """Union of per-query results, deduplicated by (clause_id, part), ranked by best score."""
        best: dict[tuple[str, int], ScoredChunk] = {}
        vectors = self.embedder.embed_queries(list(queries))
        for vector in vectors:
            for hit in self.store.search(vector, k):
                key = (hit.chunk.clause_id, hit.chunk.part)
                if key not in best or hit.score > best[key].score:
                    best[key] = hit
        return sorted(best.values(), key=lambda h: -h.score)[:k]
