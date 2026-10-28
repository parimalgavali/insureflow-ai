"""SQLAlchemy models. Task 3 adds policy_chunks; task 5 adds conversations/messages/claims."""

from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
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
