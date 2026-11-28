"""Do not let another change bypass a document confirmation still being saved."""

from fastapi import HTTPException
from sqlalchemy import select

from db.models import Attachment, EvidenceSuggestion


def require_no_pending_evidence(session, conversation_id, allowed_suggestion_id=None):
    query = (
        select(EvidenceSuggestion.id)
        .join(Attachment)
        .where(
            Attachment.conversation_id == conversation_id,
            EvidenceSuggestion.status == "applying",
        )
    )
    if allowed_suggestion_id is not None:
        query = query.where(EvidenceSuggestion.id != allowed_suggestion_id)
    if session.scalar(query.limit(1)):
        raise HTTPException(
            409, "finish the pending document confirmation before changing this claim"
        )
