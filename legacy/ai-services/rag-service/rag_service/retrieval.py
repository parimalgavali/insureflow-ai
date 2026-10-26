import re
from dataclasses import dataclass

from rag_service.chunking import DocumentChunk


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "how",
    "i",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "what",
    "when",
    "which",
}


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: DocumentChunk
    score: float


def retrieve_chunks(
    *,
    chunks: list[DocumentChunk],
    question: str,
    top_k: int,
    claim_id: str | None = None,
) -> list[RetrievedChunk]:
    question_tokens = _tokens(question)
    if not question_tokens:
        return []

    scored: list[RetrievedChunk] = []
    for chunk in chunks:
        if claim_id and chunk.claim_id and chunk.claim_id != claim_id:
            continue
        score = _score(question_tokens, chunk)
        if score > 0:
            scored.append(RetrievedChunk(chunk=chunk, score=score))
    scored.sort(key=lambda result: (-result.score, result.chunk.chunk_id))
    return scored[:top_k]


def _score(question_tokens: set[str], chunk: DocumentChunk) -> float:
    chunk_tokens = _tokens(chunk.text)
    overlap = question_tokens.intersection(chunk_tokens)
    if not overlap:
        return 0.0

    score = len(overlap) / max(len(question_tokens), 1)
    lower_text = chunk.text.lower()
    if "coverage" in question_tokens and "coverage" in lower_text:
        score += 0.15
    if "covered" in question_tokens and "covered" in lower_text:
        score += 0.15
    if {"missing", "documents"}.intersection(question_tokens) and any(
        term in lower_text for term in ["police report", "medical note", "damage photos", "repair estimate"]
    ):
        score += 0.25
    if "exclusion" in question_tokens and "excluded" in lower_text:
        score += 0.15
    return round(score, 4)


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in STOPWORDS and len(token) > 1}
