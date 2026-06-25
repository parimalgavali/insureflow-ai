from fastapi import HTTPException
import pytest

from document_intelligence.audit import InMemoryAuditStore
from document_intelligence.prompts import PromptTemplate
from document_intelligence.schemas import DocumentType, ExtractionRequest
from document_intelligence.service import DocumentIntelligenceService


class FlakyJsonProvider:
    def __init__(self) -> None:
        self.calls = 0

    def generate_json(self, prompt: PromptTemplate, payload: object, retry: bool = False) -> str:
        self.calls += 1
        if self.calls == 1:
            return "{not-json"
        return (
            '{"claimType":"MOTOR_COLLISION","damageType":"REAR_BUMPER",'
            '"thirdPartyInvolved":true,"policeReportAvailable":false,'
            '"possibleHitAndRun":true,"estimatedDamageAmount":4500,'
            '"injuryReported":false,"requiredDocuments":["POLICE_REPORT"]}'
        )


class BrokenJsonProvider:
    def generate_json(self, prompt: PromptTemplate, payload: object, retry: bool = False) -> str:
        return "{not-json"


def test_extract_retries_invalid_json_once_and_audits_success():
    audit_store = InMemoryAuditStore()
    provider = FlakyJsonProvider()
    service = DocumentIntelligenceService(provider=provider, audit_store=audit_store)

    response = service.extract(_claim_description_request())

    assert provider.calls == 2
    audit_record = audit_store.get(response.audit_id)
    assert audit_record is not None
    assert audit_record.prompt_name == "claim_description_extraction"
    assert audit_record.prompt_version == "v1"
    assert audit_record.validation_status == "VALID"
    assert audit_record.raw_response.startswith('{"claimType"')
    assert audit_record.parsed_output["claimType"] == "MOTOR_COLLISION"


def test_extract_raises_422_and_audits_failure_after_retry():
    audit_store = InMemoryAuditStore()
    service = DocumentIntelligenceService(provider=BrokenJsonProvider(), audit_store=audit_store)

    with pytest.raises(HTTPException) as exc_info:
        service.extract(_claim_description_request())

    assert exc_info.value.status_code == 422
    records = audit_store.list_records()
    assert len(records) == 1
    assert records[0].validation_status == "INVALID"
    assert records[0].parsed_output is None
    assert records[0].error_message is not None


def _claim_description_request() -> ExtractionRequest:
    return ExtractionRequest(
        claim_id="CLM-ID-001",
        claim_number="CLM-20260626-000001",
        document_id="DOC-001",
        document_type=DocumentType.CLAIM_DESCRIPTION,
        text="Rear bumper damage around 4500 EUR with no police report.",
    )
