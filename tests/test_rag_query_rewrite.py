from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag.chunking import Chunk
from rag.embeddings import BagOfWordsEmbedder
from rag.ingest import ingest
from rag.query_rewrite import NoRewriter, RecordedRewriter, make_rewriter, parse_variants
from rag.retriever import Retriever
from rag.store import InMemoryStore


def test_parse_variants_extracts_json_array_from_chatty_output():
    text = 'Sure:\n["Entwendung des Fahrzeugs", "Diebstahl Teilkasko", " "]\nHope that helps'
    assert parse_variants(text) == ["Entwendung des Fahrzeugs", "Diebstahl Teilkasko"]
    assert parse_variants("no json here") == []
    assert parse_variants("[not valid json") == []
    assert len(parse_variants(json.dumps(["a", "b", "c", "d"]))) == 3


def test_recorded_rewriter_roundtrip(tmp_path: Path):
    path = tmp_path / "rewrites.json"
    rw = RecordedRewriter(path)
    assert rw.rewrite("unknown question", "en") == []
    rw.record("Is my car covered against theft? ", ["Entwendung Fahrzeug", "Diebstahl Kasko"])
    rw.save()
    again = RecordedRewriter(path)
    assert again.rewrite("Is my car covered against theft?", "en") == [
        "Entwendung Fahrzeug",
        "Diebstahl Kasko",
    ]
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "Is my car covered against theft?": ["Entwendung Fahrzeug", "Diebstahl Kasko"]
    }


def test_make_rewriter():
    assert isinstance(make_rewriter("none"), NoRewriter)
    assert isinstance(make_rewriter("recorded"), RecordedRewriter)
    with pytest.raises(ValueError, match="unknown rewriter"):
        make_rewriter("gpt")


def test_retriever_uses_rewrites_to_find_clause_without_lexical_overlap(tmp_path: Path):
    store, embedder = InMemoryStore(), BagOfWordsEmbedder()
    ingest(
        [
            Chunk(
                "A.2.2.1.2",
                "Entwendung",
                "Versichert ist die Entwendung des Fahrzeugs",
                "A.2.2.1",
                10,
            ),
            Chunk(
                "A.2.2.1.5",
                "Glasbruch",
                "Versichert sind Bruchschäden an der Verglasung",
                "A.2.2.1",
                10,
            ),
        ],
        store,
        embedder,
    )
    rw = RecordedRewriter(tmp_path / "r.json")
    rw.record("Is my car covered against theft?", ["Entwendung des Fahrzeugs"])
    dense_only = Retriever(store, embedder).retrieve(
        "Is my car covered against theft?", k=1, lang="en"
    )
    with_rewrites = Retriever(store, embedder, rw).retrieve(
        "Is my car covered against theft?", k=1, lang="en"
    )
    assert with_rewrites[0].clause_id == "A.2.2.1.2"
    assert with_rewrites[0].score > dense_only[0].score
