from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class IngestRequest(ApiModel):
    document_id: str
    claim_id: str | None = None
    policy_id: str | None = None
    document_type: str
    title: str
    text: Annotated[str, Field(min_length=1)]
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(ApiModel):
    document_id: str
    chunk_count: int
    chunk_ids: list[str]


class QueryRequest(ApiModel):
    claim_id: str | None = None
    question: Annotated[str, Field(min_length=1)]
    top_k: int = Field(default=5, ge=1, le=10)


class SourceReference(ApiModel):
    document_id: str
    chunk_id: str
    document_type: str
    section_title: str | None = None
    page_number: int = 1
    score: float


class QueryResponse(ApiModel):
    answer: str
    sources: list[SourceReference]
    confidence: str
    requires_human_review: bool
    prompt_name: str = "rag_adjuster_assistant"
    prompt_version: str = "v1"
    audit_id: str


class ChunkResponse(ApiModel):
    document_id: str
    chunk_id: str
    claim_id: str | None = None
    policy_id: str | None = None
    document_type: str
    section_title: str | None = None
    page_number: int = 1
    chunk_index: int
    text_preview: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChunkListResponse(ApiModel):
    document_id: str
    chunks: list[ChunkResponse]
