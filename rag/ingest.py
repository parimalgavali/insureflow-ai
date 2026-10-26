"""Chunk the AKB text, embed it and write it to the vector store (idempotent by content hash).

uv run python -m rag.ingest            # Postgres via DATABASE_URL (runs Alembic migrations first)
uv run python -m rag.ingest --dry-run  # chunk + embed only, print stats
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from rag.chunking import AKB_TXT, SOURCE_ID, Chunk, chunk_akb
from rag.embeddings import Embedder, EmbedderProtocol
from rag.store import PgVectorStore, VectorStore


def ingest(
    chunks: list[Chunk], store: VectorStore, embedder: EmbedderProtocol, source: str = SOURCE_ID
) -> dict:
    """Embed only chunks with a new content hash; delete rows whose hash left the corpus."""
    existing = store.existing_hashes(source)
    fresh = [c for c in chunks if c.content_hash not in existing]
    started = time.time()
    if fresh:
        vectors = embedder.embed_passages([c.embedding_text for c in fresh])
        store.upsert(fresh, vectors)
    removed = store.delete_missing(source, {c.content_hash for c in chunks})
    return {
        "chunks": len(chunks),
        "embedded": len(fresh),
        "skipped": len(chunks) - len(fresh),
        "removed": removed,
        "seconds": round(time.time() - started, 1),
        "total_in_store": store.count(),
    }


def run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    root = Path(__file__).resolve().parents[1]
    command.upgrade(Config(str(root / "alembic.ini")), "head")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--source", type=Path, default=AKB_TXT, help="path to akb_2015.txt")
    parser.add_argument("--dry-run", action="store_true", help="do not touch the database")
    args = parser.parse_args(argv)

    if not args.source.exists():
        print(
            f"error: {args.source} not found; run `python scripts/fetch_data.py akb` first",
            file=sys.stderr,
        )
        return 1
    chunks = chunk_akb(args.source)
    embedder = Embedder()
    if args.dry_run:
        from rag.store import InMemoryStore

        stats = ingest(chunks, InMemoryStore(), embedder)
    else:
        run_migrations()
        stats = ingest(chunks, PgVectorStore(), embedder)
    print(" ".join(f"{k}={v}" for k, v in stats.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
