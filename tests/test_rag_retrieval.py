from __future__ import annotations

import os

import numpy as np
import pytest

from rag.chunking import Chunk
from rag.embeddings import BagOfWordsEmbedder
from rag.eval import (
    EvalResult,
    Question,
    evaluate,
    first_hit_rank,
    is_hit,
    load_questions,
    summarise,
)
from rag.ingest import ingest
from rag.retriever import Retriever
from rag.store import InMemoryStore, ScoredChunk

CORPUS = [
    Chunk(
        "A.2.2.1.4",
        "Zusammenstoß mit Haarwild",
        "Versichert ist der Zusammenstoß mit Haarwild Reh Wildschwein",
        "A.2.2.1",
        10,
    ),
    Chunk(
        "A.2.2.1.2",
        "Entwendung",
        "Versichert ist die Entwendung Diebstahl des Fahrzeugs",
        "A.2.2.1",
        10,
    ),
    Chunk(
        "A.2.2.1.5",
        "Glasbruch",
        "Versichert sind Bruchschäden an der Verglasung Windschutzscheibe",
        "A.2.2.1",
        10,
    ),
    Chunk(
        "E.1.1.1", "Anzeigepflicht", "Schaden innerhalb einer Woche melden anzeigen", "E.1.1", 31
    ),
]


@pytest.fixture
def retriever() -> Retriever:
    store, embedder = InMemoryStore(), BagOfWordsEmbedder()
    ingest(CORPUS, store, embedder)
    return Retriever(store, embedder)


def test_ingest_is_idempotent_and_prunes_stale_chunks():
    store, embedder = InMemoryStore(), BagOfWordsEmbedder()
    first = ingest(CORPUS, store, embedder)
    second = ingest(CORPUS, store, embedder)
    assert (first["embedded"], first["skipped"]) == (4, 0)
    assert (second["embedded"], second["skipped"], second["total_in_store"]) == (0, 4, 4)
    pruned = ingest(CORPUS[:2], store, embedder)
    assert pruned["removed"] == 2 and store.count() == 2


def test_retrieve_returns_matching_clause_first(retriever):
    hits = retriever.retrieve("Zusammenstoß mit Reh", k=3)
    assert hits[0].clause_id == "A.2.2.1.4"
    assert hits[0].score > hits[-1].score
    assert len(hits) == 3


def test_retrieve_many_unions_and_dedupes(retriever):
    hits = retriever.retrieve_many(["Diebstahl des Fahrzeugs", "Entwendung Fahrzeug"], k=2)
    ids = [h.clause_id for h in hits]
    assert ids[0] == "A.2.2.1.2" and len(ids) == len(set(ids)) <= 2


def test_search_on_empty_store_returns_nothing():
    assert InMemoryStore().search(np.zeros(64, dtype=np.float32), 5) == []


def test_is_hit_accepts_exact_and_descendants():
    assert is_hit("A.2.2.2.2", ["A.2.2.2"])
    assert is_hit("E.1.1.3", ["E.1.1"])
    assert not is_hit("A.2.2.2", ["A.2.2.2.2"])
    assert not is_hit("A.2.2.20", ["A.2.2.2"])


def test_first_hit_rank_counts_distinct_clauses():
    def sc(cid: str, part: int = 1) -> ScoredChunk:
        return ScoredChunk(Chunk(cid, "", "x", None, 1, part=part), 0.5)

    hits = [sc("A.1"), sc("A.1", 2), sc("B.2")]
    assert first_hit_rank(hits, ["B.2"]) == 2
    assert first_hit_rank(hits, ["Z.9"]) is None


def test_evaluate_and_summarise(retriever):
    questions = [
        Question("q1", "de", "Zusammenstoß mit Reh", ["A.2.2.1.4"]),
        Question("q2", "en", "windshield broken", ["Z.9"]),  # clause not in corpus → miss
        Question("q3", "de", "Schaden melden Woche", ["E.1.1"]),
    ]
    results = evaluate(retriever, questions, k=3)
    summary = summarise(results)
    assert [r.rank for r in results][0] == 1 and results[2].rank == 1
    assert summary["n"] == 3 and summary["top3_de"] == 1.0 and summary["top3_en"] == 0.0
    assert summary["top3"] == pytest.approx(2 / 3)
    assert isinstance(results[0], EvalResult)


def test_question_set_is_well_formed():
    questions = load_questions()
    assert len(questions) >= 25
    assert {q.lang for q in questions} == {"de", "en"}
    assert len({q.id for q in questions}) == len(questions)
    assert all(q.expected for q in questions)


@pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="needs Postgres with pgvector (DATABASE_URL)"
)
def test_pgvector_store_roundtrip():
    from rag.ingest import run_migrations
    from rag.store import PgVectorStore

    run_migrations()
    store = PgVectorStore()
    embedder = BagOfWordsEmbedder(dim=384)
    test_chunks = [
        Chunk(c.clause_id, c.title, c.text, c.parent_id, c.page, source="test_corpus")
        for c in CORPUS
    ]
    ingest(test_chunks, store, embedder, source="test_corpus")
    hits = Retriever(store, embedder).retrieve("Zusammenstoß mit Reh", k=2)
    assert hits[0].clause_id == "A.2.2.1.4" and hits[0].chunk.source == "test_corpus"
    assert store.delete_missing("test_corpus", set()) == 4
