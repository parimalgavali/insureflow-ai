from rag_service.retrieval import RetrievedChunk
from rag_service.schemas import SourceReference


MISSING_EVIDENCE_ANSWER = (
    "I do not have enough retrieved evidence to answer this question. "
    "Please add policy, claim, guideline, or document evidence and have an adjuster review the file."
)


def answer_question(question: str, retrieved_chunks: list[RetrievedChunk]) -> tuple[str, str, bool, list[SourceReference]]:
    if not retrieved_chunks:
        return MISSING_EVIDENCE_ANSWER, "LOW", True, []

    top_text = retrieved_chunks[0].chunk.text.lower()
    if "coverage" in top_text or "covered" in top_text:
        answer = (
            "Based on the retrieved policy coverage section, collision damage appears potentially covered "
            "when the policy was active on the loss date. Human review is required before any claim decision."
        )
    elif "police report" in top_text:
        answer = (
            "Based on the retrieved claim guideline, a police report should be requested for third-party "
            "collision claims. Human review is required before deciding whether the file is complete."
        )
    else:
        answer = (
            "Based on the retrieved evidence, the adjuster should review the cited source chunks before taking "
            "the next action. This answer is decision support only."
        )

    sources = [
        SourceReference(
            document_id=result.chunk.document_id,
            chunk_id=result.chunk.chunk_id,
            document_type=result.chunk.document_type,
            section_title=result.chunk.section_title,
            page_number=result.chunk.page_number,
            score=result.score,
        )
        for result in retrieved_chunks
    ]
    return answer, "MEDIUM", True, sources
