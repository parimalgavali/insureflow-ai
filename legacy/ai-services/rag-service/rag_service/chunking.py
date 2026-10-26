from dataclasses import dataclass, field
from typing import Any

from rag_service.schemas import IngestRequest


@dataclass(frozen=True)
class DocumentChunk:
    document_id: str
    chunk_id: str
    claim_id: str | None
    policy_id: str | None
    document_type: str
    section_title: str | None
    page_number: int
    chunk_index: int
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


def chunk_document(request: IngestRequest) -> list[DocumentChunk]:
    sections = _split_sections(request.text)
    chunks: list[DocumentChunk] = []
    for index, (section_title, body) in enumerate(sections, start=1):
        chunk_text = f"{section_title}\n{body}".strip() if section_title else body.strip()
        chunks.append(
            DocumentChunk(
                document_id=request.document_id,
                chunk_id=f"{request.document_id}-CHUNK-{index:04d}",
                claim_id=request.claim_id,
                policy_id=request.policy_id,
                document_type=request.document_type,
                section_title=section_title,
                page_number=1,
                chunk_index=index,
                text=chunk_text,
                metadata=request.metadata,
            )
        )
    return chunks


def _split_sections(text: str) -> list[tuple[str | None, str]]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    sections: list[tuple[str | None, str]] = []
    for paragraph in paragraphs:
        lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        if not lines:
            continue
        if len(lines) == 1:
            sections.append((None, lines[0]))
        else:
            sections.append((lines[0], " ".join(lines[1:])))
    return sections or [(None, text.strip())]
