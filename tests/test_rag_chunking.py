from __future__ import annotations

from pathlib import Path

import pytest

from rag.chunking import Chunk, chunk_akb, normalise_lines, parent_of, split_clauses

FIXTURE = Path(__file__).parent / "fixtures" / "akb_2015_pages1-11.txt"


@pytest.fixture(scope="module")
def chunks() -> dict[str, Chunk]:
    out: dict[str, Chunk] = {}
    for c in chunk_akb(FIXTURE):
        out.setdefault(c.clause_id, c)
    return out


def test_normalise_joins_hyphenated_line_breaks():
    lines = normalise_lines("A.1.1.1 Wir stellen Sie von Schadenersatz-\nansprüchen frei.\n")
    assert lines == [(1, "A.1.1.1 Wir stellen Sie von Schadenersatzansprüchen frei.")]


def test_normalise_keeps_hyphen_before_capitalised_continuation():
    lines = normalise_lines("Liefer- und Beförderungs-\nFristen\n")
    assert lines[0][1] == "Liefer- und Beförderungs-Fristen"


def test_normalise_tracks_page_numbers_from_separator_lines():
    raw = "_" * 40 + " 7\nA.1.2 Wer ist versichert?\nText.\n"
    assert normalise_lines(raw) == [(7, "A.1.2 Wer ist versichert?"), (7, "Text.")]


def test_parent_of():
    assert parent_of("A.2.2.1.4") == "A.2.2.1"
    assert parent_of("A.1") == "A"
    assert parent_of("Anhang 1") is None


def test_table_of_contents_is_skipped(chunks):
    first = min(chunks.values(), key=lambda c: c.page)
    assert first.page >= 6
    assert all(not c.text.rstrip().endswith((" 6", " 7", " 8")) for c in chunks.values())


def test_clause_ids_parents_and_pages(chunks):
    wild = chunks["A.2.2.1.4"]
    assert wild.parent_id == "A.2.2.1"
    assert wild.page == 10
    assert wild.title == "Zusammenstoß mit Haarwild"
    assert wild.text.startswith(
        "Versichert ist der Zusammenstoß des in Fahrt befindlichen Fahrzeugs mit Haarwild"
    )


def test_subtitle_before_clause_becomes_title(chunks):
    assert chunks["A.1.5.1"].title == "Vorsatz"
    assert chunks["A.2.2.1.3"].title.startswith("Sturm, Hagel")


def test_heading_only_clauses_are_folded_into_children(chunks):
    assert "A.2.2" not in chunks  # "Welche Ereignisse sind versichert?" has no body of its own
    assert "A.2.2 Welche Ereignisse sind versichert?" in chunks["A.2.2.1.2"].heading_chain
    assert chunks["A.2.2.1.2"].heading_chain[0].startswith("A Welche Leistungen")


def test_heading_with_body_is_kept(chunks):
    assert chunks["A.1.2"].title == "Wer ist versichert?"
    assert "Der Schutz der Kfz-Haftpflichtversicherung" in chunks["A.1.2"].text


def test_embedding_text_contains_chain_id_and_body(chunks):
    text = chunks["A.2.2.1.2"].embedding_text
    assert text.startswith("A Welche Leistungen")
    assert "\nA.2.2.1.2 Entwendung\n" in text
    assert text.endswith(chunks["A.2.2.1.2"].text)


def test_content_hash_is_stable_and_distinct(chunks):
    a, b = chunks["A.1.1.1"], chunks["A.1.1.2"]
    assert a.content_hash == Chunk(**{**a.__dict__}).content_hash
    assert a.content_hash != b.content_hash


def test_oversize_clause_is_split_into_parts():
    body = " ".join(["wort"] * 1200)
    lines = [(6, "A Welche Leistungen umfasst Ihre Kfz-Versicherung?"), (6, f"A.1.1.1 {body}")]
    parts = split_clauses(lines)
    assert [p.part for p in parts] == [1, 2, 3]
    assert all(p.clause_id == "A.1.1.1" for p in parts)
    assert sum(len(p.text.split()) for p in parts) == 1200
