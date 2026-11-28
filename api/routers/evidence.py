"""Explicit, retryable PDF analysis that only writes document suggestions."""

import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy import text as sql_text

from api.evidence import AttachmentOut, attachment_out
from api.evidence_extraction import extract_suggestions
from api.evidence_text import EvidenceTextError, prepare_evidence_pdf
from api.security import get_state, require_token
from db.models import Attachment, Conversation, EvidenceSuggestion, MessageOperation

router = APIRouter(
    prefix="/api/conversations", tags=["evidence"], dependencies=[Depends(require_token)]
)


def _load_attachment(session, conversation_id, attachment_id):
    attachment = session.scalar(
        select(Attachment).where(
            Attachment.id == attachment_id,
            Attachment.conversation_id == conversation_id,
        )
    )
    if attachment is None:
        raise HTTPException(404, "attachment not found")
    return attachment


@router.post("/{conversation_id}/attachments/{attachment_id}/extract", response_model=AttachmentOut)
def extract_evidence(
    conversation_id: uuid.UUID, attachment_id: uuid.UUID, state=Depends(get_state)
):
    with state.session() as session:
        attachment = _load_attachment(session, conversation_id, attachment_id)
        if attachment.media_type != "pdf":
            raise HTTPException(422, "verified_pdf_required")
    key = int.from_bytes(
        hashlib.sha256(b"evidence:" + attachment_id.bytes).digest()[:8], "big", signed=True
    )
    with state.engine.connect() as connection:
        acquired = connection.execute(
            sql_text("SELECT pg_try_advisory_lock(:key)"), {"key": key}
        ).scalar_one()
        connection.commit()
        if not acquired:
            raise HTTPException(409, "evidence_processing")
        try:
            with state.session() as session:
                attachment = _load_attachment(session, conversation_id, attachment_id)
                if attachment.processing_state == "ready":
                    return attachment_out(session, attachment)
                conv = session.scalar(
                    select(Conversation).where(Conversation.id == conversation_id).with_for_update()
                )
                if conv is None:
                    raise HTTPException(404, "conversation not found")
                if conv.status not in ("collecting", "assessed", "information_needed"):
                    raise HTTPException(409, "claim_already_submitted")
                if session.scalar(
                    select(MessageOperation.id)
                    .where(
                        MessageOperation.conversation_id == conversation_id,
                        MessageOperation.response.is_(None),
                    )
                    .limit(1)
                ):
                    raise HTTPException(409, "message_unfinished")
                filename, path = attachment.filename, attachment.path
                attachment.processing_state, attachment.error = "processing", None
                session.commit()
            try:
                pages = prepare_evidence_pdf(Path(path))
                suggestions = extract_suggestions(state.provider, filename, pages)
                with state.session() as session:
                    attachment = _load_attachment(session, conversation_id, attachment_id)
                    session.execute(
                        delete(EvidenceSuggestion).where(
                            EvidenceSuggestion.attachment_id == attachment_id
                        )
                    )
                    session.add_all(
                        [
                            EvidenceSuggestion(
                                attachment_id=attachment_id,
                                position=i,
                                field=s.field,
                                value=s.value,
                                page=s.page,
                                quote=s.quote,
                            )
                            for i, s in enumerate(suggestions)
                        ]
                    )
                    attachment.processing_state, attachment.error = "ready", None
                    attachment.page_count = len(pages)
                    session.commit()
                    return attachment_out(session, attachment)
            except Exception as exc:  # noqa: BLE001
                code = str(exc) if isinstance(exc, EvidenceTextError) else "extraction_failed"
                with state.session() as session:
                    attachment = _load_attachment(session, conversation_id, attachment_id)
                    session.execute(
                        delete(EvidenceSuggestion).where(
                            EvidenceSuggestion.attachment_id == attachment_id
                        )
                    )
                    attachment.processing_state, attachment.error = "failed", code
                    attachment.page_count = None
                    session.commit()
                    return attachment_out(session, attachment)
        finally:
            connection.execute(sql_text("SELECT pg_advisory_unlock(:key)"), {"key": key})
            connection.commit()
