"""Selected-policy lookup never falls through to the shared demo corpus."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.agent.schemas import Citation, ClaimCard, CoverageEvidence
from api.policy_text import search_passages
from db.models import PolicyDocument

EVENT_TERMS = {
    "collision": ["Unfall", "Kollision", "collision", "accident"],
    "hit_and_run": ["Unfall", "Fahrerflucht", "hit-and-run", "collision", "accident"],
    "theft": ["Entwendung", "Diebstahl", "theft", "stolen"],
    "vandalism": ["böswillige", "mutwillige", "vandalism"],
    "glass": ["Glasbruch", "Verglasung", "glass", "windscreen"],
    "wild_animal": ["Haarwild", "Wildschaden", "animal", "deer"],
    "storm_hail": ["Sturm", "Hagel", "storm", "hail"],
    "fire": ["Brand", "Explosion", "fire"],
}
COMMON_TERMS = [
    "Ausschluss",
    "exclusion",
    "Selbstbeteiligung",
    "deductible",
    "Anzeigepflicht",
    "reporting",
]


class PolicyCoverageStore:
    def __init__(self, engine):
        self.engine = engine

    def retrieve(self, conversation_id: str, facts, policy) -> CoverageEvidence | None:
        with Session(self.engine) as session:
            document = session.scalar(
                select(PolicyDocument).where(
                    PolicyDocument.conversation_id == uuid.UUID(conversation_id),
                    PolicyDocument.is_current.is_(True),
                )
            )
            if document is None:
                return None
            result = CoverageEvidence(
                coverage_source="uploaded_policy",
                coverage_policy_id=str(document.id),
                coverage_policy_name=document.filename,
                coverage_policy_ready=document.status == "ready",
            )
            if document.status != "ready":
                return result
            terms = EVENT_TERMS.get(facts.event_type, ["Schaden", "Deckung", "coverage", "cover"])
            queries = [*terms, *COMMON_TERMS]
            if facts.description:
                queries.append(facts.description[:1000])
            hits = [
                search_passages(session, document.conversation_id, document.id, query, limit=3)
                for query in queries
            ]
            ordered = {}
            for rank in range(3):
                for group in hits:
                    if rank < len(group):
                        passage = group[rank]
                        ordered.setdefault(passage.id, passage)
            result.retrieved = [
                Citation(
                    clause_id=f"P.{p.position + 1}",
                    title=p.section_heading or f"Page {p.page}",
                    excerpt=p.text,
                    page=p.page,
                    source="uploaded_policy",
                    document_id=str(document.id),
                    source_name=document.filename,
                )
                for p in list(ordered.values())[:8]
            ]
            return result


def coverage_source_changed(session, card: ClaimCard, conversation_id) -> bool:
    document = session.scalar(
        select(PolicyDocument).where(
            PolicyDocument.conversation_id == conversation_id, PolicyDocument.is_current.is_(True)
        )
    )
    return document is not None and (
        (document.replaces_document_id is not None and document.status != "ready")
        or card.coverage_source != "uploaded_policy"
        or card.coverage_policy_id != str(document.id)
        or card.coverage_policy_ready != (document.status == "ready")
    )


def current_coverage_card(session, card: ClaimCard, conversation_id, language: str) -> ClaimCard:
    """Read old assessments honestly; finalization must enforce this source check too."""
    if coverage_source_changed(session, card, conversation_id) and card.coverage_summary:
        message = (
            (
                "Der ausgewählte Vertrag hat sich geändert. Aktualisieren Sie die Bewertung "
                "vor dem Einreichen oder Abschließen."
            )
            if language == "de"
            else (
                "The selected policy has changed. Refresh the assessment before submitting "
                "or completing review."
            )
        )
        return card.model_copy(update={"assessment_stale": True, "assessment_error": message})
    return card
