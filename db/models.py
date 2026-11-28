"""SQLAlchemy models. Task 3 adds policy_chunks; task 5 adds conversations/messages/claims."""

from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, ForeignKeyConstraint, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from rag.embeddings import EMBEDDING_DIM


class Base(DeclarativeBase):
    pass


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    clause_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    parent_id: Mapped[str | None] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    heading_chain: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    page: Mapped[int] = mapped_column(Integer, nullable=False)
    part: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(EMBEDDING_DIM), nullable=False)


# --- task 5: conversations, messages, claims, attachments ------------------------------------
import uuid  # noqa: E402
from datetime import UTC, datetime  # noqa: E402

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint  # noqa: E402
from sqlalchemy.dialects.postgresql import JSONB, UUID  # noqa: E402
from sqlalchemy.orm import relationship  # noqa: E402


def _now() -> datetime:
    return datetime.now(UTC)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )
    language: Mapped[str] = mapped_column(String(2), default="de", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="collecting", nullable=False)
    policy: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation", order_by="Message.created_at", cascade="all, delete-orphan"
    )
    claim: Mapped[Claim | None] = relationship(back_populates="conversation", uselist=False)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    attachments: Mapped[list[Attachment]] = relationship(back_populates="message")


class Claim(Base):
    __tablename__ = "claims"
    __table_args__ = (Index("ix_claims_status_submitted_at", "status", "submitted_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    status: Mapped[str] = mapped_column(String(32), default="collecting", nullable=False)
    card: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    document_checklist: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )

    conversation: Mapped[Conversation] = relationship(back_populates="claim")
    events: Mapped[list[ClaimEvent]] = relationship(
        back_populates="claim", order_by="ClaimEvent.id", cascade="all, delete-orphan"
    )


class ClaimEvent(Base):
    __tablename__ = "claim_events"
    __table_args__ = (
        UniqueConstraint("claim_id", "operation_id", "kind", name="uq_claim_event_operation"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    claim_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    operation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    actor: Mapped[str] = mapped_column(String(32), nullable=False)
    decision: Mapped[str | None] = mapped_column(String(32))
    note: Mapped[str | None] = mapped_column(Text)
    changes: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )

    claim: Mapped[Claim] = relationship(back_populates="events")


class Attachment(Base):
    __tablename__ = "attachments"
    __table_args__ = (
        UniqueConstraint("id", "conversation_id", name="uq_attachment_conversation"),
        UniqueConstraint("replaces_attachment_id", name="uq_attachment_replacement"),
        ForeignKeyConstraint(
            ["replaces_attachment_id", "conversation_id"],
            ["attachments.id", "attachments.conversation_id"],
            name="fk_attachment_replacement_scope",
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL")
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    is_current: Mapped[bool] = mapped_column(default=True, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    replaces_attachment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    media_type: Mapped[str] = mapped_column(String(16), default="unknown", nullable=False)
    document_type: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    processing_state: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(Integer)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )

    message: Mapped[Message | None] = relationship(back_populates="attachments")


class EvidenceSuggestion(Base):
    __tablename__ = "evidence_suggestions"
    __table_args__ = (
        UniqueConstraint("attachment_id", "position", name="uq_evidence_suggestion_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attachment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attachments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    field: Mapped[str] = mapped_column(String(40), nullable=False)
    value: Mapped[str | float | bool] = mapped_column(JSONB, nullable=False)
    page: Mapped[int] = mapped_column(Integer, nullable=False)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    expected_value: Mapped[str | float | bool | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)


class MessageOperation(Base):
    """Durable identity and response for one customer message, including its upload."""

    __tablename__ = "message_operations"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    user_text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(2), nullable=False)
    has_attachment: Mapped[bool] = mapped_column(nullable=False)
    has_photo: Mapped[bool] = mapped_column(default=False, nullable=False)
    base_message_count: Mapped[int] = mapped_column(Integer, nullable=False)
    response: Mapped[list[str] | None] = mapped_column(JSONB)


class PolicyDocument(Base):
    __tablename__ = "policy_documents"
    __table_args__ = (
        UniqueConstraint("id", "conversation_id", name="uq_policy_document_conversation"),
        ForeignKeyConstraint(
            ["replaces_document_id", "conversation_id"],
            ["policy_documents.id", "policy_documents.conversation_id"],
            name="fk_policy_replacement_scope",
            deferrable=True,
            initially="DEFERRED",
        ),
        Index(
            "uq_policy_current_conversation",
            "conversation_id",
            unique=True,
            postgresql_where=text("is_current"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    is_current: Mapped[bool] = mapped_column(default=True, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    replaces_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded")
    error: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(Integer)
    passage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )


class PolicyPassage(Base):
    __tablename__ = "policy_passages"
    __table_args__ = (
        ForeignKeyConstraint(
            ["document_id", "conversation_id"],
            ["policy_documents.id", "policy_documents.conversation_id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("document_id", "position", name="uq_policy_passage_position"),
        Index("ix_policy_passages_scope", "conversation_id", "document_id"),
        Index("ix_policy_passages_search", "search_vector", postgresql_using="gin"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    page: Mapped[int] = mapped_column(Integer, nullable=False)
    section_heading: Mapped[str | None] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    search_vector = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('simple', coalesce(section_heading, '') || ' ' || text)", persisted=True
        ),
    )
