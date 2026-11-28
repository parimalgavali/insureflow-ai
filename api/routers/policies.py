"""Policy uploads are separate from claim evidence and do not imply policy-based answers."""

import hashlib
import uuid
from io import BytesIO
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from pypdf import PdfReader
from sqlalchemy import delete, select
from sqlalchemy import text as sql_text

from api.policy_text import PolicyTextError, prepare_pdf
from api.security import get_state, require_token
from db.models import Conversation, MessageOperation, PolicyDocument, PolicyPassage

router = APIRouter(
    prefix="/api/conversations", tags=["policies"], dependencies=[Depends(require_token)]
)


class PolicyDocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    size_bytes: int
    status: str
    error: str | None
    page_count: int | None
    passage_count: int


class PolicySelection(BaseModel):
    coverage_source: Literal["standard_demo"] = "standard_demo"
    document: PolicyDocumentOut | None = None
    max_upload_bytes: int


def _selection(document, state):
    return PolicySelection(
        document=PolicyDocumentOut.model_validate(document, from_attributes=True)
        if document
        else None,
        max_upload_bytes=state.settings.max_upload_bytes,
    )


@router.get("/{conversation_id}/policy", response_model=PolicySelection)
def get_policy(conversation_id: uuid.UUID, state=Depends(get_state)):
    with state.session() as session:
        if session.get(Conversation, conversation_id) is None:
            raise HTTPException(404, "conversation not found")
        document = session.scalar(
            select(PolicyDocument).where(PolicyDocument.conversation_id == conversation_id)
        )
        return _selection(document, state)


def _validate_pdf(data: bytes):
    if not data.startswith(b"%PDF-"):
        raise HTTPException(422, "invalid_pdf")
    try:
        pdf = PdfReader(BytesIO(data))
        if pdf.is_encrypted:
            raise HTTPException(422, "encrypted_pdf")
        if not 0 < len(pdf.pages) <= 300:
            raise HTTPException(422, "unsupported_page_count")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(422, "invalid_pdf") from exc


@router.post("/{conversation_id}/policy", response_model=PolicySelection)
def upload_policy(
    conversation_id: uuid.UUID, file: Annotated[UploadFile, File()], state=Depends(get_state)
):
    filename = Path((file.filename or "policy.pdf").replace("\\", "/")).name
    if file.content_type != "application/pdf" or not filename.lower().endswith(".pdf"):
        raise HTTPException(415, "pdf_required")
    if len(filename) > 255:
        raise HTTPException(422, "invalid_filename")
    data = file.file.read(state.settings.max_upload_bytes + 1)
    if len(data) > state.settings.max_upload_bytes:
        raise HTTPException(413, "file_too_large")
    _validate_pdf(data)
    digest = hashlib.sha256(data).hexdigest()
    target = None
    try:
        with state.session() as session:
            conv = session.scalar(
                select(Conversation).where(Conversation.id == conversation_id).with_for_update()
            )
            if conv is None:
                raise HTTPException(404, "conversation not found")
            existing = session.scalar(
                select(PolicyDocument).where(PolicyDocument.conversation_id == conversation_id)
            )
            if existing:
                if existing.content_hash == digest:
                    return _selection(existing, state)
                raise HTTPException(409, "policy_already_uploaded")
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
            directory = state.settings.upload_dir / "policies" / str(conversation_id)
            directory.mkdir(parents=True, exist_ok=True)
            target = directory / f"{uuid.uuid4().hex}.pdf"
            target.write_bytes(data)
            document = PolicyDocument(
                conversation_id=conversation_id,
                filename=filename,
                content_hash=digest,
                path=str(target),
                size_bytes=len(data),
                status="uploaded",
            )
            session.add(document)
            session.commit()
            return _selection(document, state)
    except BaseException:
        if target is not None:
            target.unlink(missing_ok=True)
        raise


@router.post("/{conversation_id}/policy/prepare", response_model=PolicySelection)
def prepare_policy(conversation_id: uuid.UUID, state=Depends(get_state)):
    with state.session() as session:
        document = session.scalar(
            select(PolicyDocument).where(PolicyDocument.conversation_id == conversation_id)
        )
        if document is None:
            raise HTTPException(404, "policy not found")
        document_id, path = document.id, document.path
    key = int.from_bytes(
        hashlib.sha256(b"policy:" + document_id.bytes).digest()[:8], "big", signed=True
    )
    with state.engine.connect() as connection:
        acquired = connection.execute(
            sql_text("SELECT pg_try_advisory_lock(:key)"), {"key": key}
        ).scalar_one()
        connection.commit()
        if not acquired:
            raise HTTPException(409, "policy_processing")
        try:
            with state.session() as session:
                document = session.get(PolicyDocument, document_id)
                if document.status == "ready":
                    return _selection(document, state)
                document.status, document.error = "processing", None
                session.commit()
            try:
                pages, passages = prepare_pdf(Path(path))
                with state.session() as session:
                    document = session.get(PolicyDocument, document_id)
                    session.execute(
                        delete(PolicyPassage).where(PolicyPassage.document_id == document_id)
                    )
                    session.add_all(
                        [
                            PolicyPassage(
                                document_id=document_id,
                                conversation_id=conversation_id,
                                position=i,
                                page=p.page,
                                section_heading=p.section_heading,
                                text=p.text,
                            )
                            for i, p in enumerate(passages)
                        ]
                    )
                    document.status, document.error = "ready", None
                    document.page_count, document.passage_count = pages, len(passages)
                    session.commit()
                    return _selection(document, state)
            except Exception as exc:  # noqa: BLE001
                code = str(exc) if isinstance(exc, PolicyTextError) else "processing_failed"
                with state.session() as session:
                    document = session.get(PolicyDocument, document_id)
                    session.execute(
                        delete(PolicyPassage).where(PolicyPassage.document_id == document_id)
                    )
                    document.status, document.error = "failed", code
                    document.page_count, document.passage_count = None, 0
                    session.commit()
                    return _selection(document, state)
        finally:
            connection.execute(sql_text("SELECT pg_advisory_unlock(:key)"), {"key": key})
            connection.commit()
