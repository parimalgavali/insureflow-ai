from rag_service.answering import answer_question
from rag_service.audit import InMemoryRagAuditStore
from rag_service.chunking import DocumentChunk, chunk_document
from rag_service.retrieval import retrieve_chunks
from rag_service.schemas import (
    ChunkListResponse,
    ChunkResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)
from rag_service.store import InMemoryChunkStore


PROMPT_NAME = "rag_adjuster_assistant"
PROMPT_VERSION = "v1"


class RagAssistantService:
    def __init__(
        self,
        chunk_store: InMemoryChunkStore | None = None,
        audit_store: InMemoryRagAuditStore | None = None,
    ) -> None:
        self.chunk_store = chunk_store or InMemoryChunkStore()
        self.audit_store = audit_store or InMemoryRagAuditStore()

    def ingest(self, request: IngestRequest) -> IngestResponse:
        chunks = chunk_document(request)
        self.chunk_store.upsert_document(request.document_id, chunks)
        return IngestResponse(
            document_id=request.document_id,
            chunk_count=len(chunks),
            chunk_ids=[chunk.chunk_id for chunk in chunks],
        )

    def list_chunks(self, document_id: str) -> ChunkListResponse:
        return ChunkListResponse(
            document_id=document_id,
            chunks=[_chunk_response(chunk) for chunk in self.chunk_store.list_document_chunks(document_id)],
        )

    def query(self, request: QueryRequest) -> QueryResponse:
        retrieved = retrieve_chunks(
            chunks=self.chunk_store.all_chunks(),
            question=request.question,
            top_k=request.top_k,
            claim_id=request.claim_id,
        )
        answer, confidence, requires_human_review, sources = answer_question(request.question, retrieved)
        audit = self.audit_store.add(
            claim_id=request.claim_id,
            question=request.question,
            prompt_name=PROMPT_NAME,
            prompt_version=PROMPT_VERSION,
            retrieved_chunk_ids=[result.chunk.chunk_id for result in retrieved],
            answer=answer,
            confidence=confidence,
            requires_human_review=requires_human_review,
        )
        return QueryResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            requires_human_review=requires_human_review,
            prompt_name=PROMPT_NAME,
            prompt_version=PROMPT_VERSION,
            audit_id=audit.audit_id,
        )


def _chunk_response(chunk: DocumentChunk) -> ChunkResponse:
    return ChunkResponse(
        document_id=chunk.document_id,
        chunk_id=chunk.chunk_id,
        claim_id=chunk.claim_id,
        policy_id=chunk.policy_id,
        document_type=chunk.document_type,
        section_title=chunk.section_title,
        page_number=chunk.page_number,
        chunk_index=chunk.chunk_index,
        text_preview=chunk.text[:240],
        metadata=chunk.metadata,
    )
