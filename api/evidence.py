"""Safe attachment metadata shared by customer and reviewer claim responses."""

import uuid

from pydantic import BaseModel, Field
from sqlalchemy import select

from db.models import Attachment, EvidenceSuggestion


class SuggestionOut(BaseModel):
    id: uuid.UUID
    field: str
    value: str | float | bool
    page: int
    quote: str
    status: str
    source_document_id: uuid.UUID
    source_name: str


class AttachmentOut(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    media_type: str
    document_type: str
    processing_state: str
    size_bytes: int
    error: str | None
    page_count: int | None = None
    suggestions: list[SuggestionOut] = Field(default_factory=list)


def attachments_out(session, conversation_id) -> list[AttachmentOut]:
    rows = list(
        session.scalars(
            select(Attachment)
            .where(Attachment.conversation_id == conversation_id)
            .order_by(Attachment.created_at, Attachment.id)
        )
    )
    grouped = {row.id: [] for row in rows}
    if rows:
        for suggestion in session.scalars(
            select(EvidenceSuggestion)
            .where(EvidenceSuggestion.attachment_id.in_(grouped))
            .order_by(EvidenceSuggestion.position)
        ):
            grouped[suggestion.attachment_id].append(suggestion)
    return [attachment_out(session, row, grouped[row.id]) for row in rows]


def attachment_out(session, row, suggestions=None):
    if suggestions is None:
        suggestions = session.scalars(
            select(EvidenceSuggestion)
            .where(EvidenceSuggestion.attachment_id == row.id)
            .order_by(EvidenceSuggestion.position)
        )
    output = AttachmentOut.model_validate(row, from_attributes=True)
    output.suggestions = [
        SuggestionOut(
            id=s.id,
            field=s.field,
            value=s.value,
            page=s.page,
            quote=s.quote,
            status=s.status,
            source_document_id=row.id,
            source_name=row.filename,
        )
        for s in suggestions
    ]
    return output
