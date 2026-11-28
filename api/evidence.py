"""Safe attachment metadata shared by customer and reviewer claim responses."""

import uuid

from pydantic import BaseModel
from sqlalchemy import select

from db.models import Attachment


class AttachmentOut(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    media_type: str
    document_type: str
    processing_state: str
    size_bytes: int
    error: str | None


def attachments_out(session, conversation_id) -> list[AttachmentOut]:
    rows = session.scalars(
        select(Attachment)
        .where(Attachment.conversation_id == conversation_id)
        .order_by(Attachment.created_at, Attachment.id)
    )
    return [AttachmentOut.model_validate(row, from_attributes=True) for row in rows]
