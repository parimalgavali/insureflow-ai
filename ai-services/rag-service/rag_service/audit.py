from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class RagAuditRecord(BaseModel):
    audit_id: str
    claim_id: str | None
    question: str
    prompt_name: str
    prompt_version: str
    retrieved_chunk_ids: list[str]
    answer: str
    confidence: str
    requires_human_review: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InMemoryRagAuditStore:
    def __init__(self) -> None:
        self._records: dict[str, RagAuditRecord] = {}

    def add(
        self,
        *,
        claim_id: str | None,
        question: str,
        prompt_name: str,
        prompt_version: str,
        retrieved_chunk_ids: list[str],
        answer: str,
        confidence: str,
        requires_human_review: bool,
    ) -> RagAuditRecord:
        audit_id = f"RAG-AUD-{uuid4()}"
        record = RagAuditRecord(
            audit_id=audit_id,
            claim_id=claim_id,
            question=question,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            retrieved_chunk_ids=retrieved_chunk_ids,
            answer=answer,
            confidence=confidence,
            requires_human_review=requires_human_review,
        )
        self._records[audit_id] = record
        return record

    def get(self, audit_id: str) -> RagAuditRecord | None:
        return self._records.get(audit_id)
