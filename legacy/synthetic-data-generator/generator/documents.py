from __future__ import annotations

from generator.models import Claim, ClaimDocument, SyntheticDocument


def render_document(claim: Claim, claim_document: ClaimDocument) -> SyntheticDocument:
    police_text = "a police report is available" if claim.police_report_available else "no police report is available"
    injury_text = "injury was reported" if claim.injury_reported else "no injury was reported"
    third_party_text = "a third party was involved" if claim.third_party_involved else "no third party was involved"

    templates = {
        "FNOL_STATEMENT": (
            f"FNOL statement for claim {claim.claim_number}: loss occurred in {claim.loss_city} "
            f"on {claim.loss_date}. Estimated damage is EUR {claim.estimated_damage_eur}. "
            f"{injury_text}; {third_party_text}; {police_text}."
        ),
        "REPAIR_INVOICE": (
            f"Repair invoice references claim {claim.claim_number} for damage in {claim.loss_city}. "
            f"The workshop estimate totals EUR {claim.estimated_damage_eur} for the {claim.claim_type} loss."
        ),
        "POLICE_REPORT": (
            f"Police report note for {claim.loss_city} incident on {claim.loss_date}: "
            f"{third_party_text}; {injury_text}; report availability: {claim.police_report_available}."
        ),
        "MEDICAL_REPORT": (
            f"Medical report for claim {claim.claim_number}: {injury_text} after the {claim.loss_date} "
            f"incident in {claim.loss_city}. Third party flag: {claim.third_party_involved}."
        ),
        "CUSTOMER_EMAIL": (
            f"Customer email about claim {claim.claim_number}: {claim.description} "
            f"The loss city was {claim.loss_city}, loss date {claim.loss_date}, and {police_text}."
        ),
        "ADJUSTER_NOTE": (
            f"Adjuster note for claim {claim.claim_number}: estimated damage EUR {claim.estimated_damage_eur}; "
            f"{injury_text}; {third_party_text}; police report flag {claim.police_report_available}."
        ),
    }

    text = templates.get(claim_document.document_type, templates["FNOL_STATEMENT"])
    return SyntheticDocument(
        document_id=claim_document.document_id,
        claim_id=claim.claim_id,
        document_type=claim_document.document_type,
        text=text,
    )
