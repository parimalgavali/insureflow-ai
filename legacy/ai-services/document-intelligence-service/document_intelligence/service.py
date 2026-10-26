import json
from json import JSONDecodeError
from typing import Any, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel, ValidationError
from pydantic.alias_generators import to_camel

from document_intelligence.audit import InMemoryAuditStore, PromptAuditRecord
from document_intelligence.prompts import PromptTemplate, get_prompt
from document_intelligence.provider import (
    DeterministicDocumentIntelligenceProvider,
    DocumentIntelligenceProvider,
)
from document_intelligence.schemas import (
    ClaimDescriptionExtraction,
    ClaimSummaryRequest,
    ClaimSummaryResponse,
    DocumentType,
    ExtractionRequest,
    ExtractionResponse,
    MissingDocumentsRequest,
    MissingDocumentsResponse,
    RepairInvoiceExtraction,
)

T = TypeVar("T", bound=BaseModel)


class DocumentIntelligenceService:
    def __init__(
        self,
        provider: DocumentIntelligenceProvider | None = None,
        audit_store: InMemoryAuditStore | None = None,
    ) -> None:
        self.provider = provider or DeterministicDocumentIntelligenceProvider()
        self.audit_store = audit_store or InMemoryAuditStore()

    def extract(self, request: ExtractionRequest) -> ExtractionResponse:
        prompt_name, schema = _schema_for_document_type(request.document_type)
        prompt = get_prompt(prompt_name)
        parsed, audit = self._generate_validated(
            prompt=prompt,
            payload=request,
            schema=schema,
            claim_id=request.claim_id,
            claim_number=request.claim_number,
            document_id=request.document_id,
            document_type=request.document_type.value,
        )
        return ExtractionResponse(
            claim_id=request.claim_id,
            claim_number=request.claim_number,
            document_id=request.document_id,
            document_type=request.document_type,
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            model_name=prompt.model_name,
            audit_id=audit.audit_id,
            extracted_fields=parsed.model_dump(by_alias=True),
            validation_warnings=[],
        )

    def missing_check(self, request: MissingDocumentsRequest) -> MissingDocumentsResponse:
        prompt = get_prompt("missing_documents")
        parsed, audit = self._generate_validated(
            prompt=prompt,
            payload=request,
            schema=_MissingDocumentsPayload,
            claim_id=request.claim_id,
            claim_number=request.claim_number,
            document_id=None,
            document_type=None,
        )
        return MissingDocumentsResponse(
            claim_id=request.claim_id,
            claim_number=request.claim_number,
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            audit_id=audit.audit_id,
            missing_documents=parsed.missing_documents,
            explanation=parsed.explanation,
            requires_human_review=parsed.requires_human_review,
        )

    def summarize(self, request: ClaimSummaryRequest) -> ClaimSummaryResponse:
        prompt = get_prompt("claim_summary")
        parsed, audit = self._generate_validated(
            prompt=prompt,
            payload=request,
            schema=_ClaimSummaryPayload,
            claim_id=request.claim_id,
            claim_number=request.claim_number,
            document_id=None,
            document_type=None,
        )
        return ClaimSummaryResponse(
            claim_id=request.claim_id,
            claim_number=request.claim_number,
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            audit_id=audit.audit_id,
            sections=parsed.sections,
            summary_text=parsed.summary_text,
        )

    def _generate_validated(
        self,
        *,
        prompt: PromptTemplate,
        payload: BaseModel,
        schema: type[T],
        claim_id: str,
        claim_number: str,
        document_id: str | None,
        document_type: str | None,
    ) -> tuple[T, PromptAuditRecord]:
        last_error: str | None = None
        last_response = ""
        for attempt in range(2):
            retry = attempt > 0
            rendered_prompt = prompt.render(payload.model_dump(by_alias=True), retry=retry)
            raw_response = self.provider.generate_json(prompt, payload, retry=retry)
            last_response = raw_response
            try:
                parsed_json = json.loads(raw_response)
                parsed = schema.model_validate(parsed_json)
                audit = self.audit_store.add(
                    claim_id=claim_id,
                    claim_number=claim_number,
                    document_id=document_id,
                    document_type=document_type,
                    prompt_name=prompt.name,
                    prompt_version=prompt.version,
                    model_name=prompt.model_name,
                    rendered_prompt=rendered_prompt,
                    raw_response=raw_response,
                    parsed_output=parsed.model_dump(by_alias=True),
                    validation_status="VALID",
                )
                return parsed, audit
            except (JSONDecodeError, ValidationError) as exc:
                last_error = str(exc)

        rendered_prompt = prompt.render(payload.model_dump(by_alias=True), retry=True)
        self.audit_store.add(
            claim_id=claim_id,
            claim_number=claim_number,
            document_id=document_id,
            document_type=document_type,
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            model_name=prompt.model_name,
            rendered_prompt=rendered_prompt,
            raw_response=last_response,
            parsed_output=None,
            validation_status="INVALID",
            error_message=last_error,
        )
        raise HTTPException(status_code=422, detail="Document intelligence response failed validation after retry.")


class _MissingDocumentsPayload(BaseModel):
    missing_documents: list[str]
    explanation: str
    requires_human_review: bool

    model_config = {"alias_generator": to_camel, "populate_by_name": True}


class _ClaimSummaryPayload(BaseModel):
    sections: Any
    summary_text: str

    model_config = {"alias_generator": to_camel, "populate_by_name": True}


def _schema_for_document_type(document_type: DocumentType) -> tuple[str, type[BaseModel]]:
    if document_type == DocumentType.CLAIM_DESCRIPTION:
        return "claim_description_extraction", ClaimDescriptionExtraction
    if document_type == DocumentType.REPAIR_INVOICE:
        return "repair_invoice_extraction", RepairInvoiceExtraction
    return "claim_description_extraction", ClaimDescriptionExtraction
