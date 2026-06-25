import json
import re
from typing import Protocol

from document_intelligence.prompts import PromptTemplate
from document_intelligence.schemas import (
    ClaimSummaryRequest,
    ExtractionRequest,
    MissingDocumentsRequest,
)


class DocumentIntelligenceProvider(Protocol):
    def generate_json(self, prompt: PromptTemplate, payload: object, retry: bool = False) -> str:
        """Return a JSON string for the requested prompt."""


class DeterministicDocumentIntelligenceProvider:
    def generate_json(self, prompt: PromptTemplate, payload: object, retry: bool = False) -> str:
        if prompt.name == "claim_description_extraction":
            return json.dumps(_extract_claim_description(payload))
        if prompt.name == "repair_invoice_extraction":
            return json.dumps(_extract_repair_invoice(payload))
        if prompt.name == "missing_documents":
            return json.dumps(_missing_documents(payload))
        if prompt.name == "claim_summary":
            return json.dumps(_claim_summary(payload))
        return json.dumps({})


def _extract_claim_description(payload: object) -> dict[str, object]:
    request = _as_model(payload, ExtractionRequest)
    text = request.text
    normalized = text.lower()
    amount = _first_int(r"(\d{3,7})\s*(?:eur|euro|€)", normalized)
    third_party = any(term in normalized for term in ["another car", "third party", "other driver", "hit my"])
    police_available = "police report" in normalized and not any(
        term in normalized for term in ["no police report", "without police report", "missing police report"]
    )
    possible_hit_and_run = any(term in normalized for term in ["left the scene", "hit and run", "hit-and-run"])
    injury_reported = any(term in normalized for term in ["injury", "injured", "medical", "hospital"])
    damage_type = "REAR_BUMPER" if "rear bumper" in normalized else "UNKNOWN"
    claim_type = "MOTOR_COLLISION" if any(term in normalized for term in ["car", "bumper", "driving"]) else "UNKNOWN"
    required_documents = ["DAMAGE_PHOTOS"]
    if third_party and not police_available:
        required_documents.insert(0, "POLICE_REPORT")
    if claim_type == "MOTOR_COLLISION":
        required_documents.append("REPAIR_ESTIMATE")
    if injury_reported:
        required_documents.append("MEDICAL_NOTE")

    return {
        "claimType": claim_type,
        "damageType": damage_type,
        "thirdPartyInvolved": third_party,
        "policeReportAvailable": police_available,
        "possibleHitAndRun": possible_hit_and_run,
        "estimatedDamageAmount": amount,
        "injuryReported": injury_reported,
        "requiredDocuments": _unique(required_documents),
    }


def _extract_repair_invoice(payload: object) -> dict[str, object]:
    request = _as_model(payload, ExtractionRequest)
    text = request.text
    return {
        "invoiceNumber": _first_match(r"\b(INV-[A-Z0-9-]+)\b", text),
        "repairShop": _first_match(r"from\s+(.+?)(?:\.|,| Labor| Parts| Tax| Total)", text),
        "laborCost": _first_int(r"Labor cost\s+(\d{1,7})\s*(?:EUR|euro|€)", text, flags=re.IGNORECASE),
        "partsCost": _first_int(r"Parts cost\s+(\d{1,7})\s*(?:EUR|euro|€)", text, flags=re.IGNORECASE),
        "taxAmount": _first_int(r"Tax\s+(\d{1,7})\s*(?:EUR|euro|€)", text, flags=re.IGNORECASE),
        "totalAmount": _first_int(r"Total\s+(\d{1,7})\s*(?:EUR|euro|€)", text, flags=re.IGNORECASE),
        "currency": "EUR",
    }


def _missing_documents(payload: object) -> dict[str, object]:
    request = _as_model(payload, MissingDocumentsRequest)
    known = set(request.known_documents)
    missing: list[str] = []
    if request.third_party_involved and not request.police_report_available and "POLICE_REPORT" not in known:
        missing.append("POLICE_REPORT")
    if request.claim_type == "MOTOR_COLLISION" and "REPAIR_ESTIMATE" not in known:
        missing.append("REPAIR_ESTIMATE")
    if request.injury_reported and "MEDICAL_NOTE" not in known:
        missing.append("MEDICAL_NOTE")

    explanation_parts = []
    if "POLICE_REPORT" in missing:
        explanation_parts.append("Police report should be requested because a third party is involved.")
    if "REPAIR_ESTIMATE" in missing:
        explanation_parts.append("Repair estimate should be requested to validate the claimed damage amount.")
    if "MEDICAL_NOTE" in missing:
        explanation_parts.append("Medical note should be requested because injury was reported.")
    explanation = " ".join(explanation_parts) or "No required documents appear to be missing from the supplied context."

    return {
        "missingDocuments": missing,
        "explanation": explanation,
        "requiresHumanReview": bool(missing),
    }


def _claim_summary(payload: object) -> dict[str, object]:
    request = _as_model(payload, ClaimSummaryRequest)
    documents = _join_list(request.documents_received, "No documents recorded.")
    missing = _join_list(request.missing_documents, "No missing documents identified.")
    inconsistencies = _join_list(request.key_inconsistencies, "No key inconsistencies identified.")
    sections = {
        "claimOverview": f"Claim {request.claim_number} is a {request.claim_type} claim.",
        "policyAndCoverageStatus": (
            f"The policy status is {request.policy_status} and the current coverage status is {request.coverage_status}."
        ),
        "incidentDetails": request.incident_details,
        "documentsReceived": documents,
        "missingDocuments": missing,
        "aiRiskScores": (
            f"Severity is {request.triage.severity}, fraud risk is {request.triage.fraud}, "
            f"and litigation risk is {request.triage.litigation}."
        ),
        "keyInconsistencies": inconsistencies,
        "recommendedNextAction": request.recommended_next_action,
        "humanReviewWarning": (
            "This summary is decision support only. A qualified adjuster must review the claim before any decision."
        ),
    }
    return {
        "sections": sections,
        "summaryText": " ".join(sections.values()),
    }


def _as_model[T](payload: object, model_type: type[T]) -> T:
    if isinstance(payload, model_type):
        return payload
    return model_type.model_validate(payload)


def _first_match(pattern: str, text: str, flags: int = 0) -> str | None:
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None


def _first_int(pattern: str, text: str, flags: int = 0) -> int | None:
    match = re.search(pattern, text, flags)
    return int(match.group(1)) if match else None


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _join_list(values: list[str], empty: str) -> str:
    return ", ".join(values) if values else empty
