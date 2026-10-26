"""Vector stores for policy chunks: Postgres/pgvector for the app, in-memory for tests and eval."""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from rag.chunking import Chunk

DEFAULT_DATABASE_URL = "postgresql+psycopg://claimpilot:claimpilot@localhost:5432/claimpilot"


def database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


@dataclass
class ScoredChunk:
    chunk: Chunk
    score: float  # cosine similarity in [-1, 1]; higher is better

    @property
    def clause_id(self) -> str:
        return self.chunk.clause_id


class VectorStore(Protocol):
    def upsert(self, chunks: Sequence[Chunk], vectors: np.ndarray) -> int: ...

    def search(self, vector: np.ndarray, k: int) -> list[ScoredChunk]: ...

    def existing_hashes(self, source: str) -> set[str]: ...

    def delete_missing(self, source: str, keep_hashes: set[str]) -> int: ...

    def count(self) -> int: ...


class InMemoryStore:
    def __init__(self) -> None:
        self._chunks: dict[str, Chunk] = {}
        self._vectors: dict[str, np.ndarray] = {}

    def upsert(self, chunks: Sequence[Chunk], vectors: np.ndarray) -> int:
        for chunk, vector in zip(chunks, vectors, strict=True):
            self._chunks[chunk.content_hash] = chunk
            self._vectors[chunk.content_hash] = np.asarray(vector, dtype=np.float32)
        return len(chunks)

    def search(self, vector: np.ndarray, k: int) -> list[ScoredChunk]:
        if not self._chunks:
            return []
        hashes = list(self._chunks)
        matrix = np.stack([self._vectors[h] for h in hashes])
        scores = matrix @ np.asarray(vector, dtype=np.float32)
        order = np.argsort(-scores)[:k]
        return [ScoredChunk(self._chunks[hashes[i]], float(scores[i])) for i in order]

    def existing_hashes(self, source: str) -> set[str]:
        return {h for h, c in self._chunks.items() if c.source == source}

    def delete_missing(self, source: str, keep_hashes: set[str]) -> int:
        stale = [h for h, c in self._chunks.items() if c.source == source and h not in keep_hashes]
        for h in stale:
            del self._chunks[h]
            del self._vectors[h]
        return len(stale)

    def count(self) -> int:
        return len(self._chunks)


class PgVectorStore:
    """`policy_chunks` table (see db/models.py); schema is created by Alembic, not here."""

    def __init__(self, url: str | None = None, engine=None):
        from sqlalchemy import create_engine

        self.engine = engine or create_engine(url or database_url())

    def upsert(self, chunks: Sequence[Chunk], vectors: np.ndarray) -> int:
        from sqlalchemy.dialects.postgresql import insert

        from db.models import PolicyChunk

        rows = [
            {
                "content_hash": c.content_hash,
                "source": c.source,
                "clause_id": c.clause_id,
                "parent_id": c.parent_id,
                "title": c.title,
                "heading_chain": c.heading_chain,
                "page": c.page,
                "part": c.part,
                "text": c.text,
                "embedding": np.asarray(v, dtype=np.float32).tolist(),
            }
            for c, v in zip(chunks, vectors, strict=True)
        ]
        if not rows:
            return 0
        stmt = insert(PolicyChunk).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[PolicyChunk.content_hash],
            set_={k: getattr(stmt.excluded, k) for k in rows[0] if k != "content_hash"},
        )
        with self.engine.begin() as conn:
            conn.execute(stmt)
        return len(rows)

    def search(self, vector: np.ndarray, k: int) -> list[ScoredChunk]:
        from sqlalchemy import select

        from db.models import PolicyChunk

        query_vec = np.asarray(vector, dtype=np.float32).tolist()
        distance = PolicyChunk.embedding.cosine_distance(query_vec).label("distance")
        stmt = select(PolicyChunk, distance).order_by(distance).limit(k)
        with self.engine.connect() as conn:
            rows = conn.execute(stmt).all()
        return [ScoredChunk(_row_to_chunk(row), 1.0 - float(row.distance)) for row in rows]

    def existing_hashes(self, source: str) -> set[str]:
        from sqlalchemy import select

        from db.models import PolicyChunk

        with self.engine.connect() as conn:
            return set(
                conn.execute(
                    select(PolicyChunk.content_hash).where(PolicyChunk.source == source)
                ).scalars()
            )

    def delete_missing(self, source: str, keep_hashes: set[str]) -> int:
        from sqlalchemy import delete

        from db.models import PolicyChunk

        stmt = delete(PolicyChunk).where(PolicyChunk.source == source)
        if keep_hashes:
            stmt = stmt.where(PolicyChunk.content_hash.not_in(keep_hashes))
        with self.engine.begin() as conn:
            return conn.execute(stmt).rowcount

    def count(self) -> int:
        from sqlalchemy import func, select

        from db.models import PolicyChunk

        with self.engine.connect() as conn:
            return int(conn.execute(select(func.count()).select_from(PolicyChunk)).scalar_one())


def _row_to_chunk(row) -> Chunk:
    return Chunk(
        clause_id=row.clause_id,
        title=row.title,
        text=row.text,
        parent_id=row.parent_id,
        page=row.page,
        heading_chain=list(row.heading_chain or []),
        part=row.part,
        source=row.source,
    )
