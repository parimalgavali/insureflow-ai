from rag_service.chunking import DocumentChunk


class InMemoryChunkStore:
    def __init__(self) -> None:
        self._chunks_by_document: dict[str, list[DocumentChunk]] = {}

    def upsert_document(self, document_id: str, chunks: list[DocumentChunk]) -> None:
        self._chunks_by_document[document_id] = chunks

    def list_document_chunks(self, document_id: str) -> list[DocumentChunk]:
        return list(self._chunks_by_document.get(document_id, []))

    def all_chunks(self) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        for document_chunks in self._chunks_by_document.values():
            chunks.extend(document_chunks)
        return chunks

    def clear(self) -> None:
        self._chunks_by_document.clear()
