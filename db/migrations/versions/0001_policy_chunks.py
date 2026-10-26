"""policy_chunks table with pgvector embedding + HNSW index

Revision ID: 0001
Revises:
Create Date: 2026-10-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "policy_chunks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("content_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("clause_id", sa.String(32), nullable=False),
        sa.Column("parent_id", sa.String(32)),
        sa.Column("title", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "heading_chain", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("part", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
    )
    op.create_index("ix_policy_chunks_source", "policy_chunks", ["source"])
    op.create_index("ix_policy_chunks_clause_id", "policy_chunks", ["clause_id"])
    op.execute(
        "CREATE INDEX ix_policy_chunks_embedding_hnsw ON policy_chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.drop_table("policy_chunks")
