from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class DocumentType(StrEnum):
    CLAIM_DESCRIPTION = "CLAIM_DESCRIPTION"
    REPAIR_INVOICE = "REPAIR_INVOICE"
    POLICE_REPORT = "POLICE_REPORT"
    MEDICAL_NOTE = "MEDICAL_NOTE"
    POLICY_DOCUMENT = "POLICY_DOCUMENT"
    CUSTOMER_EMAIL = "CUSTOMER_EMAIL"
    ADJUSTER_NOTE = "ADJUSTER_NOTE"


class ExtractionRequest(ApiModel):
    claim_id: str
    claim_number: str
    document_id: str | None = None
    document_type: DocumentType
    text: Annotated[str, Field(min_length=1)]
    known_documents: list[str] = Field(default_factory=list)


class ClaimDescriptionExtraction(ApiModel):
    claim_type: str
    damage_type: str
    third_party_involved: bool
    police_report_available: bool
    possible_hit_and_run: bool
    estimated_damage_amount: int | None = None
    injury_reported: bool
    required_documents: list[str] = Field(default_factory=list)


class RepairInvoiceExtraction(ApiModel):
    invoice_number: str | None = None
    repair_shop: str | None = None
    labor_cost: int | None = None
    parts_cost: int | None = None
    tax_amount: int | None = None
    total_amount: int | None = None
    currency: str = "EUR"


class ExtractionResponse(ApiModel):
    claim_id: str
    claim_number: str
    document_id: str | None = None
    document_type: DocumentType
    prompt_name: str
    prompt_version: str
    model_name: str
    audit_id: str
    extracted_fields: dict[str, Any]
    validation_warnings: list[str] = Field(default_factory=list)


class MissingDocumentsRequest(ApiModel):
    claim_id: str
    claim_number: str
    claim_type: str
    injury_reported: bool = False
    third_party_involved: bool = False
    police_report_available: bool = False
    known_documents: list[str] = Field(default_factory=list)


class MissingDocumentsResponse(ApiModel):
    claim_id: str
    claim_number: str
    prompt_name: str
    prompt_version: str
    audit_id: str
    missing_documents: list[str]
    explanation: str
    requires_human_review: bool


class TriageSnapshot(ApiModel):
    severity: str
    fraud: str
    litigation: str


class ClaimSummaryRequest(ApiModel):
    claim_id: str
    claim_number: str
    claim_type: str
    policy_status: str
    coverage_status: str
    incident_details: str
    documents_received: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    triage: TriageSnapshot
    key_inconsistencies: list[str] = Field(default_factory=list)
    recommended_next_action: str


class ClaimSummarySections(ApiModel):
    claim_overview: str
    policy_and_coverage_status: str
    incident_details: str
    documents_received: str
    missing_documents: str
    ai_risk_scores: str
    key_inconsistencies: str
    recommended_next_action: str
    human_review_warning: str


class ClaimSummaryResponse(ApiModel):
    claim_id: str
    claim_number: str
    prompt_name: str
    prompt_version: str
    audit_id: str
    sections: ClaimSummarySections
    summary_text: str
