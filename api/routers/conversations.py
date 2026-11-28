"""Conversations: create, read, and send a message that streams agent events over SSE."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy import text as sql_text
from sqlalchemy.orm import object_session, selectinload

from api import sse
from api.agent.graph import thread_config
from api.agent.required_facts import missing_facts
from api.agent.schemas import ChatMessage, ClaimCard, Language, PolicyContext
from api.checklist import DocumentChecklistItem, checklist_out, sync_assessment_requests
from api.evidence import AttachmentOut, attachments_out
from api.evidence_decisions import require_no_pending_evidence
from api.evidence_files import DocumentType, EvidenceFileError, safe_upload_name, validate_upload
from api.history import HistoryEntry, history_out
from api.policy_coverage import coverage_source_changed, current_coverage_card
from api.security import get_state, require_token
from db.models import Attachment, Claim, Conversation, Message, MessageOperation

log = logging.getLogger("claimpilot.api")
router = APIRouter(
    prefix="/api/conversations", tags=["conversations"], dependencies=[Depends(require_token)]
)

GREETING = {
    "de": "Hallo! Ich bin ClaimPilot. Beschreiben Sie mir einfach in Ihren Worten, was mit "
    "Ihrem Fahrzeug passiert ist – ich stelle die nötigen Rückfragen und fasse den Fall für Sie "
    "zusammen.",
    "en": "Hi! I'm ClaimPilot. Just tell me in your own words what happened to your vehicle – "
    "I'll ask what's missing and put the claim together for you.",
}
ALLOWED_UPLOAD_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


class CreateConversation(BaseModel):
    language: Language = "de"
    policy: PolicyContext = Field(default_factory=PolicyContext)


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: str


class ConversationOut(BaseModel):
    id: uuid.UUID
    language: str
    status: str
    policy: PolicyContext
    messages: list[MessageOut]
    claim_id: uuid.UUID | None = None
    card: ClaimCard | None = None
    history: list[HistoryEntry]
    missing: list[str]
    pending_operation_id: uuid.UUID | None = None
    attachments: list[AttachmentOut] = Field(default_factory=list)
    document_checklist: list[DocumentChecklistItem] = Field(default_factory=list)


def _conversation_out(conv: Conversation) -> ConversationOut:
    card = ClaimCard.model_validate(conv.claim.card) if conv.claim and conv.claim.card else None
    if card is not None:
        card = current_coverage_card(object_session(conv), card, conv.id, conv.language)
    pending = object_session(conv).scalar(
        select(MessageOperation.id)
        .where(
            MessageOperation.conversation_id == conv.id,
            MessageOperation.response.is_(None),
        )
        .limit(1)
    )
    return ConversationOut(
        pending_operation_id=pending,
        attachments=attachments_out(object_session(conv), conv.id),
        document_checklist=checklist_out(object_session(conv), conv.claim) if conv.claim else [],
        id=conv.id,
        language=conv.language,
        status=conv.status,
        policy=PolicyContext.model_validate(conv.policy or {}),
        messages=[
            MessageOut(id=m.id, role=m.role, content=m.content, created_at=m.created_at.isoformat())
            for m in conv.messages
        ],
        claim_id=conv.claim.id if conv.claim else None,
        card=card,
        history=history_out(conv.claim) if conv.claim else [],
        missing=missing_facts(card.facts) if card else [],
    )


def _load(session, conversation_id: uuid.UUID) -> Conversation:
    conv = session.get(
        Conversation,
        conversation_id,
        options=[selectinload(Conversation.messages), selectinload(Conversation.claim)],
    )
    if conv is None:
        raise HTTPException(404, "conversation not found")
    return conv


@router.post("", status_code=201, response_model=ConversationOut)
def create_conversation(body: CreateConversation, state=Depends(get_state)) -> ConversationOut:
    with state.session() as session:
        conv = Conversation(language=body.language, policy=body.policy.model_dump())
        conv.messages.append(Message(role="assistant", content=GREETING[body.language]))
        conv.claim = Claim(status="collecting", card={})
        session.add(conv)
        session.commit()
        return _conversation_out(_load(session, conv.id))


@router.get("/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: uuid.UUID, state=Depends(get_state)) -> ConversationOut:
    with state.session() as session:
        return _conversation_out(_load(session, conversation_id))


@router.post("/{conversation_id}/messages")
def post_message(
    conversation_id: uuid.UUID,
    text: Annotated[str, Form(min_length=1, max_length=4000)],
    file: Annotated[UploadFile | None, File()] = None,
    language: Annotated[Language | None, Form()] = None,
    operation_id: Annotated[uuid.UUID | None, Form()] = None,
    document_type: Annotated[DocumentType | None, Form()] = None,
    state=Depends(get_state),
) -> StreamingResponse:
    operation_id = operation_id or uuid.uuid4()
    data = b""
    if file is None and document_type is not None:
        raise HTTPException(422, "document_type_requires_file")
    if file is not None:
        if file.content_type not in ALLOWED_UPLOAD_TYPES:
            raise HTTPException(415, "unsupported upload type")
        data = file.file.read(state.settings.max_upload_bytes + 1)
        if len(data) > state.settings.max_upload_bytes:
            raise HTTPException(413, "file too large")
        file.file.seek(0)
    fingerprint = hashlib.sha256(
        json.dumps(
            [text, language, file.filename if file else None, file.content_type if file else None]
            + ([document_type] if document_type is not None else []),
            ensure_ascii=False,
        ).encode()
        + b"\0"
        + data
    ).hexdigest()
    media_type = None
    safe_name = Path((file.filename or "upload").replace("\\", "/")).name if file else None
    with state.session() as session:
        if session.get(Conversation, conversation_id) is None:
            raise HTTPException(404, "conversation not found")
        previous = session.get(MessageOperation, (conversation_id, operation_id))
        if previous is not None and previous.fingerprint != fingerprint:
            raise HTTPException(409, "retry must use the original message and attachment")
    if file is not None and previous is None:
        try:
            safe_name = safe_upload_name(file.filename)
            media_type = validate_upload(safe_name, file.content_type, data)
        except EvidenceFileError as exc:
            raise HTTPException(exc.status, exc.code) from exc
        document_type = document_type or (
            "damage_photo" if media_type == "image" else "other_document"
        )
        if document_type == "damage_photo" and media_type != "image":
            raise HTTPException(422, "damage_photo_requires_image")
    attachment = None
    try:
        with state.session() as session:
            locked = session.scalar(
                select(Conversation).where(Conversation.id == conversation_id).with_for_update()
            )
            if locked is None:
                raise HTTPException(404, "conversation not found")
            conv = _load(session, conversation_id)
            operation = session.get(MessageOperation, (conversation_id, operation_id))
            if operation is not None:
                if operation.fingerprint != fingerprint:
                    raise HTTPException(409, "retry must use the original message and attachment")
            else:
                pending = session.scalar(
                    select(MessageOperation.id)
                    .where(
                        MessageOperation.conversation_id == conversation_id,
                        MessageOperation.response.is_(None),
                    )
                    .limit(1)
                )
                if pending:
                    raise HTTPException(409, "retry the unfinished message first")
                if conv.status not in ("collecting", "information_needed"):
                    raise HTTPException(409, "claim assessment is complete; use the claim actions")
                require_no_pending_evidence(session, conversation_id)
                if language:
                    conv.language = language
                if file is not None and media_type is None:
                    raise HTTPException(409, "saved upload changed; retry the original operation")
                attachment = (
                    _store_upload(
                        state,
                        conv.id,
                        safe_name,
                        file.content_type,
                        data,
                        media_type,
                        document_type,
                    )
                    if file
                    else None
                )
                user_text = (
                    text
                    if attachment is None
                    else f"{text}\n[Attachment: {attachment.filename} ({attachment.content_type})]"
                )
                message = Message(role="user", content=user_text)
                conv.messages.append(message)
                if attachment is not None:
                    attachment.message = message
                    session.add(attachment)
                snapshot = state.graph.get_state(thread_config(str(conversation_id)))
                operation = MessageOperation(
                    conversation_id=conversation_id,
                    id=operation_id,
                    fingerprint=fingerprint,
                    user_text=user_text,
                    language=conv.language,
                    has_attachment=attachment is not None,
                    has_photo=attachment is not None
                    and attachment.media_type == "image"
                    and attachment.document_type == "damage_photo",
                    base_message_count=len(snapshot.values.get("messages", [])),
                )
                session.add(operation)
                session.commit()
    except BaseException:
        if attachment is not None:
            Path(attachment.path).unlink(missing_ok=True)
        raise
    return StreamingResponse(
        _stream_operation(state, conversation_id, operation_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{conversation_id}/messages/{operation_id}/retry")
def retry_saved_message(
    conversation_id: uuid.UUID, operation_id: uuid.UUID, state=Depends(get_state)
):
    """Resume saved input after reload without asking for the upload again."""
    with state.session() as session:
        _load(session, conversation_id)
        if session.get(MessageOperation, (conversation_id, operation_id)) is None:
            raise HTTPException(404, "saved message not found")
    return StreamingResponse(
        _stream_operation(state, conversation_id, operation_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _store_upload(state, conversation_id, filename, content_type, data, media_type, document_type):
    target_dir = state.settings.upload_dir / str(conversation_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{uuid.uuid4().hex}_{filename}"
    target.write_bytes(data)
    return Attachment(
        conversation_id=conversation_id,
        filename=filename,
        content_hash=hashlib.sha256(data).hexdigest(),
        content_type=content_type,
        size_bytes=len(data),
        path=str(target),
        media_type=media_type,
        document_type=document_type,
        processing_state="stored",
    )


def _stream_operation(state, conversation_id: uuid.UUID, operation_id: uuid.UUID):
    # Session advisory lock spans graph execution but no transaction spans an SSE yield.
    # A disconnected client releases the lock in finally; another worker can resume.
    lock_key = int.from_bytes(
        hashlib.sha256(conversation_id.bytes).digest()[:8], "big", signed=True
    )
    with state.engine.connect() as connection:
        acquired = connection.execute(
            sql_text("SELECT pg_try_advisory_lock(:key)"), {"key": lock_key}
        ).scalar_one()
        connection.commit()
        if not acquired:
            yield sse.encode(
                "error", {"message": "This message is still processing. Please retry shortly."}
            )
            return
        try:
            with state.session() as session:
                operation = session.get(MessageOperation, (conversation_id, operation_id))
                if operation.response is not None:
                    response = operation.response
                else:
                    response = None
                policy = PolicyContext.model_validate(_load(session, conversation_id).policy or {})
            if response is not None:
                yield from _replay_operation(state, conversation_id, response)
                return
            config = thread_config(str(conversation_id))
            snapshot = state.graph.get_state(config)
            same = snapshot.values.get("message_operation_id") == str(operation_id)
            payload = (
                None
                if same
                else {
                    "messages": [ChatMessage(role="user", content=operation.user_text)],
                    "message_operation_id": str(operation_id),
                    "policy": policy,
                    "language": operation.language,
                    "attachments": int(operation.has_attachment),
                    "photo_attached_this_turn": operation.has_photo,
                }
            )
            if not same or (
                snapshot.next and snapshot.next not in (("submit",), ("human_review",))
            ):
                for update in state.graph.stream(payload, config, stream_mode="updates"):
                    for node, node_data in update.items():
                        yield from _events_for(node, node_data, [])
            final = state.graph.get_state(config).values
            assistant_texts = [
                m.content
                for m in final.get("messages", [])[operation.base_message_count + 1 :]
                if m.role == "assistant"
            ]
            with state.session() as session:
                saved = session.get(MessageOperation, (conversation_id, operation_id))
                conv = _load(session, conversation_id)
                for content in assistant_texts:
                    conv.messages.append(Message(role="assistant", content=content))
                conv.status = final.get("status", conv.status)
                card = final.get("card") or ClaimCard(
                    facts=final["facts"], policy=policy, status=conv.status
                )
                card = current_coverage_card(session, card, conv.id, conv.language)
                conv.claim.card = card.model_dump(mode="json")
                sync_assessment_requests(conv.claim)
                conv.claim.status = conv.status
                response = [
                    sse.encode("facts", {"facts": final["facts"], "language": operation.language}),
                    sse.encode("missing", {"missing": final.get("missing", [])}),
                ]
                response.append(
                    sse.encode(
                        "risk_availability",
                        {"status": card.risk_status, "missing": card.risk_missing},
                    )
                )
                if final.get("card") is not None:
                    response.extend(
                        [
                            sse.encode("citations", {"citations": card.citations}),
                            sse.encode("risk", {"risk": card.risk}),
                            sse.encode("card", {"card": card}),
                        ]
                    )
                if assistant_texts:
                    response.append(sse.encode("question", {"text": assistant_texts[-1]}))
                response.append(
                    sse.encode(
                        "done",
                        {
                            "status": conv.status,
                            "claim_id": str(conv.claim.id),
                            "awaiting_review": conv.status == "awaiting_review",
                        },
                    )
                )
                saved.response = response
                session.commit()
            yield from response
        except Exception:
            log.exception("agent turn failed")
            yield sse.encode(
                "error", {"message": "Your message could not be completed. Please retry."}
            )
        finally:
            connection.execute(sql_text("SELECT pg_advisory_unlock(:key)"), {"key": lock_key})
            connection.commit()


def _replay_operation(state, conversation_id, response):
    """Keep saved replies scoped and explicitly historical after a policy change."""
    records = []
    with state.session() as session:
        conv = _load(session, conversation_id)
        warning = None
        for record in response:
            kind, payload = record.split("\ndata: ", 1)
            data = json.loads(payload)
            if kind == "event: card":
                card = ClaimCard.model_validate(data["card"])
                if coverage_source_changed(session, card, conversation_id):
                    card = current_coverage_card(session, card, conversation_id, conv.language)
                    warning = card.assessment_error
                    data["card"] = card.model_dump(mode="json")
            records.append((kind.removeprefix("event: "), data))
    for kind, data in records:
        if warning and kind == "question":
            data["text"] = f"{warning}\n\n{data['text']}"
        yield sse.encode(kind, data)


def _events_for(node: str, data: Any, assistant_texts: list[str]):
    if node == "__interrupt__":
        return
    if not isinstance(data, dict):
        return
    if node == "extract" and data.get("facts") is not None:
        yield sse.encode("facts", {"facts": data["facts"], "language": data.get("language")})
        yield sse.encode(
            "risk_availability", {"status": data["risk_status"], "missing": data["risk_missing"]}
        )
    elif node == "check_missing":
        yield sse.encode("missing", {"missing": data.get("missing", [])})
    elif node == "ask_followup":
        text = data["messages"][-1].content
        assistant_texts.append(text)
        for piece in sse.chunk_words(text):
            yield sse.encode("token", {"text": piece})
        yield sse.encode("question", {"text": text})
    elif node == "retrieve":
        yield sse.encode("citations", {"citations": data.get("retrieved", [])})
    elif node == "score_risk":
        yield sse.encode("risk", {"risk": data.get("risk")})
        yield sse.encode(
            "risk_availability", {"status": data["risk_status"], "missing": data["risk_missing"]}
        )
    elif node == "compose":
        text = data["messages"][-1].content
        assistant_texts.append(text)
        for piece in sse.chunk_words(text):
            yield sse.encode("token", {"text": piece})
        yield sse.encode("card", {"card": data["card"]})
    elif node == "human_review":
        yield sse.encode("card", {"card": data["card"]})
