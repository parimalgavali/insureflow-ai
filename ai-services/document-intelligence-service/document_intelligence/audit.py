from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class PromptAuditRecord(BaseModel):
    audit_id: str
    claim_id: str
    claim_number: str
    document_id: str | None = None
    document_type: str | None = None
    prompt_name: str
    prompt_version: str
    model_name: str
    rendered_prompt: str
    raw_response: str
    parsed_output: dict[str, Any] | None = None
    validation_status: str
    error_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InMemoryAuditStore:
    def __init__(self) -> None:
        self._records: dict[str, PromptAuditRecord] = {}

    def add(
        self,
        *,
        claim_id: str,
        claim_number: str,
        document_id: str | None,
        document_type: str | None,
        prompt_name: str,
        prompt_version: str,
        model_name: str,
        rendered_prompt: str,
        raw_response: str,
        parsed_output: dict[str, Any] | None,
        validation_status: str,
        error_message: str | None = None,
    ) -> PromptAuditRecord:
        audit_id = f"AUD-{uuid4()}"
        record = PromptAuditRecord(
            audit_id=audit_id,
            claim_id=claim_id,
            claim_number=claim_number,
            document_id=document_id,
            document_type=document_type,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            model_name=model_name,
            rendered_prompt=rendered_prompt,
            raw_response=raw_response,
            parsed_output=parsed_output,
            validation_status=validation_status,
            error_message=error_message,
        )
        self._records[audit_id] = record
        return record

    def get(self, audit_id: str) -> PromptAuditRecord | None:
        return self._records.get(audit_id)

    def list_records(self) -> list[PromptAuditRecord]:
        return list(self._records.values())

    def clear(self) -> None:
        self._records.clear()
