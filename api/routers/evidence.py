"""Explicit, retryable PDF analysis that only writes document suggestions."""

import hashlib
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy import text as sql_text

from api.evidence import AttachmentOut, attachment_out
from api.evidence_decisions import require_no_pending_evidence
from api.evidence_extraction import extract_suggestions
from api.evidence_files import EvidenceFileError, safe_upload_name, validate_upload
from api.evidence_text import EvidenceTextError, prepare_evidence_pdf
from api.history import record_event
from api.security import get_state, require_token
from db.models import Attachment, Claim, Conversation, EvidenceSuggestion, MessageOperation

router = APIRouter(
    prefix="/api/conversations", tags=["evidence"], dependencies=[Depends(require_token)]
)


def _load_attachment(session, conversation_id, attachment_id, *, current_only=False):
    attachment = session.scalar(
        select(Attachment).where(
            Attachment.id == attachment_id,
            Attachment.conversation_id == conversation_id,
        )
    )
    if attachment is None:
        raise HTTPException(404, "attachment not found")
    if current_only and not attachment.is_current:
        raise HTTPException(409, "attachment_replaced")
    return attachment


def evidence_lock_key(attachment_id):
    return int.from_bytes(
        hashlib.sha256(b"evidence:" + attachment_id.bytes).digest()[:8], "big", signed=True
    )


@router.post("/{conversation_id}/attachments/{attachment_id}/extract", response_model=AttachmentOut)
def extract_evidence(
    conversation_id: uuid.UUID, attachment_id: uuid.UUID, state=Depends(get_state)
):
    with state.session() as session:
        attachment = _load_attachment(session, conversation_id, attachment_id, current_only=True)
        if attachment.media_type != "pdf":
            raise HTTPException(422, "verified_pdf_required")
    key = evidence_lock_key(attachment_id)
    with state.engine.connect() as connection:
        acquired = connection.execute(
            sql_text("SELECT pg_try_advisory_lock(:key)"), {"key": key}
        ).scalar_one()
        connection.commit()
        if not acquired:
            raise HTTPException(409, "evidence_processing")
        try:
            with state.session() as session:
                attachment = _load_attachment(
                    session, conversation_id, attachment_id, current_only=True
                )
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
                require_no_pending_evidence(session, conversation_id)
                filename, path = attachment.filename, attachment.path
                attachment.processing_state, attachment.error = "processing", None
                session.commit()
            try:
                pages = prepare_evidence_pdf(Path(path))
                suggestions = extract_suggestions(state.provider, filename, pages)
                with state.session() as session:
                    attachment = _load_attachment(
                        session, conversation_id, attachment_id, current_only=True
                    )
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
                    session.flush()
                    output = attachment_out(session, attachment)
                    session.commit()
                    return output
            except Exception as exc:  # noqa: BLE001
                code = str(exc) if isinstance(exc, EvidenceTextError) else "extraction_failed"
                with state.session() as session:
                    attachment = _load_attachment(
                        session, conversation_id, attachment_id, current_only=True
                    )
                    if attachment.processing_state == "ready":
                        # A connection can fail after COMMIT succeeds. Keep completed work.
                        return attachment_out(session, attachment)
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


@router.put("/{conversation_id}/attachments/{attachment_id}", response_model=AttachmentOut)
def replace_evidence_pdf(
    conversation_id: uuid.UUID,
    attachment_id: uuid.UUID,
    file: Annotated[UploadFile, File()],
    state=Depends(get_state),
):
    with state.session() as session:
        old = _load_attachment(session, conversation_id, attachment_id)
        if old.content_type != "application/pdf":
            raise HTTPException(422, "pdf_replacement_required")
    if file.content_type != "application/pdf":
        raise HTTPException(415, "pdf_required")
    data = file.file.read(state.settings.max_upload_bytes + 1)
    if len(data) > state.settings.max_upload_bytes:
        raise HTTPException(413, "file_too_large")
    try:
        filename = safe_upload_name(file.filename)
        validate_upload(filename, file.content_type, data)
    except EvidenceFileError as exc:
        raise HTTPException(exc.status, exc.code) from exc
    digest = hashlib.sha256(data).hexdigest()
    key, target = evidence_lock_key(attachment_id), None
    with state.engine.connect() as connection:
        acquired = connection.execute(
            sql_text("SELECT pg_try_advisory_lock(:key)"), {"key": key}
        ).scalar_one()
        connection.commit()
        if not acquired:
            raise HTTPException(409, "evidence_processing")
        try:
            with state.session() as session:
                # Claim first, then conversation: the same order as confirmations/submission.
                claim = session.scalar(
                    select(Claim).where(Claim.conversation_id == conversation_id).with_for_update()
                )
                conv = session.scalar(
                    select(Conversation).where(Conversation.id == conversation_id).with_for_update()
                )
                if claim is None or conv is None:
                    raise HTTPException(404, "conversation not found")
                old = _load_attachment(session, conversation_id, attachment_id)
                if not old.is_current:
                    replacement = session.scalar(
                        select(Attachment).where(
                            Attachment.conversation_id == conversation_id,
                            Attachment.replaces_attachment_id == attachment_id,
                        )
                    )
                    if (
                        replacement
                        and replacement.content_hash == digest
                        and replacement.filename == filename
                    ):
                        return attachment_out(session, replacement)
                    raise HTTPException(409, "attachment_replaced")
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
                require_no_pending_evidence(session, conversation_id)
                if old.content_hash == digest:
                    raise HTTPException(422, "same_copy")
                directory = state.settings.upload_dir / str(conversation_id)
                directory.mkdir(parents=True, exist_ok=True)
                target = directory / f"{uuid.uuid4().hex}.pdf"
                target.write_bytes(data)
                old.is_current = False
                replacement = Attachment(
                    conversation_id=conversation_id,
                    filename=filename,
                    content_type="application/pdf",
                    media_type="pdf",
                    document_type=old.document_type
                    if old.document_type in ("repair_estimate", "police_report", "other_document")
                    else "other_document",
                    processing_state="stored",
                    content_hash=digest,
                    size_bytes=len(data),
                    path=str(target),
                    is_current=True,
                    revision=old.revision + 1,
                    replaces_attachment_id=old.id,
                )
                session.add(replacement)
                for suggestion in session.scalars(
                    select(EvidenceSuggestion).where(
                        EvidenceSuggestion.attachment_id == old.id,
                        EvidenceSuggestion.status == "pending",
                    )
                ):
                    suggestion.status = "superseded"
                session.flush()
                record_event(
                    session,
                    claim,
                    operation_id="replacement-" + replacement.id.hex,
                    kind="evidence_replaced",
                    actor="customer",
                    note=f"{old.filename} → {filename}",
                )
                output = attachment_out(session, replacement)
                session.commit()
                return output
        except BaseException:
            if target is not None:
                _remove_uncommitted_copy(state, target)
            raise
        finally:
            connection.execute(sql_text("SELECT pg_advisory_unlock(:key)"), {"key": key})
            connection.commit()


def _remove_uncommitted_copy(state, target):
    # An exception from COMMIT can mean the acknowledgement was lost. Delete the
    # private file only after a fresh database read proves no saved row uses it.
    try:
        with state.session() as session:
            saved = session.scalar(
                select(Attachment.id).where(Attachment.path == str(target)).limit(1)
            )
    except Exception:  # noqa: BLE001
        return  # Keeping an uncertain private file is safer than breaking a saved copy.
    if saved is None:
        target.unlink(missing_ok=True)
