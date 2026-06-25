from fastapi import FastAPI

from document_intelligence.schemas import (
    ClaimSummaryRequest,
    ClaimSummaryResponse,
    ExtractionRequest,
    ExtractionResponse,
    MissingDocumentsRequest,
    MissingDocumentsResponse,
)
from document_intelligence.service import DocumentIntelligenceService

app = FastAPI(title="InsureFlow AI Document Intelligence Service", version="0.1.0")
service = DocumentIntelligenceService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "document-intelligence-service"}


@app.get("/ai/v1/documents/health")
def document_health() -> dict[str, str]:
    return health()


@app.post("/ai/v1/documents/extract", response_model=ExtractionResponse)
def extract(request: ExtractionRequest) -> ExtractionResponse:
    return service.extract(request)


@app.post("/ai/v1/documents/missing-check", response_model=MissingDocumentsResponse)
def missing_check(request: MissingDocumentsRequest) -> MissingDocumentsResponse:
    return service.missing_check(request)


@app.post("/ai/v1/documents/summarize", response_model=ClaimSummaryResponse)
def summarize(request: ClaimSummaryRequest) -> ClaimSummaryResponse:
    return service.summarize(request)
