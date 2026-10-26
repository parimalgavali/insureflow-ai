from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    version: str
    model_name: str
    temperature: float
    schema_name: str
    template: str

    def render(self, payload: dict[str, Any], retry: bool = False) -> str:
        retry_instruction = "\nReturn valid JSON only. Do not include markdown." if retry else ""
        return self.template.format(payload=payload) + retry_instruction


PROMPT_REGISTRY: dict[str, PromptTemplate] = {
    "claim_description_extraction": PromptTemplate(
        name="claim_description_extraction",
        version="v1",
        model_name="deterministic-document-intelligence",
        temperature=0.0,
        schema_name="ClaimDescriptionExtraction",
        template=(
            "Extract structured claim facts from this FNOL description. "
            "Use the ClaimDescriptionExtraction JSON schema.\nPayload: {payload}"
        ),
    ),
    "repair_invoice_extraction": PromptTemplate(
        name="repair_invoice_extraction",
        version="v1",
        model_name="deterministic-document-intelligence",
        temperature=0.0,
        schema_name="RepairInvoiceExtraction",
        template=(
            "Extract repair invoice fields from this document text. "
            "Use the RepairInvoiceExtraction JSON schema.\nPayload: {payload}"
        ),
    ),
    "missing_documents": PromptTemplate(
        name="missing_documents",
        version="v1",
        model_name="deterministic-document-intelligence",
        temperature=0.0,
        schema_name="MissingDocumentsResponse",
        template=(
            "Identify missing claim documents and explain what an adjuster should request. "
            "Use the MissingDocumentsResponse JSON schema.\nPayload: {payload}"
        ),
    ),
    "claim_summary": PromptTemplate(
        name="claim_summary",
        version="v1",
        model_name="deterministic-document-intelligence",
        temperature=0.0,
        schema_name="ClaimSummaryResponse",
        template=(
            "Create an adjuster-ready claim summary with required sections. "
            "Use the ClaimSummaryResponse JSON schema.\nPayload: {payload}"
        ),
    ),
}


def get_prompt(name: str) -> PromptTemplate:
    return PROMPT_REGISTRY[name]
