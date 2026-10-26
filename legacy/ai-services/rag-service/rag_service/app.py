from fastapi import FastAPI

from rag_service.schemas import (
    ChunkListResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)
from rag_service.service import RagAssistantService

app = FastAPI(title="InsureFlow AI RAG Assistant Service", version="0.1.0")
service = RagAssistantService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "rag-service"}


@app.post("/ai/v1/rag/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    return service.ingest(request)


@app.post("/ai/v1/rag/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    return service.query(request)


@app.get("/ai/v1/rag/documents/{document_id}/chunks", response_model=ChunkListResponse)
def list_document_chunks(document_id: str) -> ChunkListResponse:
    return service.list_chunks(document_id)
