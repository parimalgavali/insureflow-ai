"""Conversations: create, read, and send a message that streams agent events over SSE."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import selectinload

from api import sse
from api.agent.graph import pending_interrupt, thread_config
from api.agent.schemas import ChatMessage, ClaimCard, Language, PolicyContext
from api.security import get_state, require_token
from db.models import Attachment, Claim, Conversation, Message

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


def _conversation_out(conv: Conversation) -> ConversationOut:
    card = ClaimCard.model_validate(conv.claim.card) if conv.claim and conv.claim.card else None
    return ConversationOut(
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
    state=Depends(get_state),
) -> StreamingResponse:
    with state.session() as session:
        conv = _load(session, conversation_id)
        if conv.status == "reviewed":
            raise HTTPException(409, "conversation already reviewed")
        attachment = _store_upload(state, conv.id, file) if file is not None else None
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
        session.commit()
        language, policy = conv.language, PolicyContext.model_validate(conv.policy or {})

    return StreamingResponse(
        _stream_turn(state, conversation_id, user_text, language, policy, attachment is not None),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _store_upload(state, conversation_id: uuid.UUID, file: UploadFile) -> Attachment:
    if file.content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(415, f"unsupported upload type {file.content_type}")
    data = file.file.read(state.settings.max_upload_bytes + 1)
    if len(data) > state.settings.max_upload_bytes:
        raise HTTPException(413, "file too large")
    safe_name = Path(file.filename or "upload").name
    target_dir = state.settings.upload_dir / str(conversation_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{uuid.uuid4().hex}_{safe_name}"
    target.write_bytes(data)
    return Attachment(
        conversation_id=conversation_id,
        filename=safe_name,
        content_type=file.content_type,
        size_bytes=len(data),
        path=str(target),
    )


def _stream_turn(
    state,
    conversation_id: uuid.UUID,
    user_text: str,
    language: str,
    policy: PolicyContext,
    has_attachment: bool,
):
    thread = str(conversation_id)
    payload: dict[str, Any] = {
        "messages": [ChatMessage(role="user", content=user_text)],
        "policy": policy,
        "language": language,
        "attachments": 1 if has_attachment else 0,
    }
    assistant_texts: list[str] = []
    final: dict[str, Any] = {}
    try:
        for update in state.graph.stream(payload, thread_config(thread), stream_mode="updates"):
            for node, data in update.items():
                yield from _events_for(node, data, assistant_texts)
        final = state.graph.get_state(thread_config(thread)).values
        interrupted = (
            pending_interrupt(
                {"__interrupt__": state.graph.get_state(thread_config(thread)).tasks[0].interrupts}
            )
            if state.graph.get_state(thread_config(thread)).tasks
            else None
        )
        with state.session() as session:
            conv = _load(session, conversation_id)
            for text in assistant_texts:
                conv.messages.append(Message(role="assistant", content=text))
            conv.status = final.get("status", conv.status)
            card = final.get("card")
            if card is not None:
                conv.claim.card = card.model_dump(mode="json")
                conv.claim.status = card.status
            else:
                conv.claim.status = conv.status
                conv.claim.card = (
                    {**(conv.claim.card or {}), "facts": final["facts"].model_dump(mode="json")}
                    if final.get("facts")
                    else conv.claim.card
                )
            session.commit()
            claim_id = str(conv.claim.id)
        yield sse.encode(
            "done",
            {
                "status": final.get("status"),
                "claim_id": claim_id,
                "awaiting_review": interrupted is not None,
            },
        )
    except Exception as exc:  # noqa: BLE001
        log.exception("agent turn failed")
        yield sse.encode("error", {"message": f"{exc.__class__.__name__}: {exc}"})


def _events_for(node: str, data: Any, assistant_texts: list[str]):
    if node == "__interrupt__":
        return
    if not isinstance(data, dict):
        return
    if node == "extract" and data.get("facts") is not None:
        yield sse.encode("facts", {"facts": data["facts"], "language": data.get("language")})
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
    elif node == "compose":
        text = data["messages"][-1].content
        assistant_texts.append(text)
        for piece in sse.chunk_words(text):
            yield sse.encode("token", {"text": piece})
        yield sse.encode("card", {"card": data["card"]})
    elif node == "human_review":
        yield sse.encode("card", {"card": data["card"]})
