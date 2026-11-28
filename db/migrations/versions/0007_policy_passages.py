"""Page-referenced, scoped full-text search for uploaded policies."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("policy_documents", sa.Column("page_count", sa.Integer()))
    op.add_column(
        "policy_documents",
        sa.Column("passage_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_unique_constraint(
        "uq_policy_document_conversation", "policy_documents", ["id", "conversation_id"]
    )
    op.create_table(
        "policy_passages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("section_heading", sa.Text()),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('simple', coalesce(section_heading, '') || ' ' || text)",
                persisted=True,
            ),
        ),
        sa.ForeignKeyConstraint(
            ["document_id", "conversation_id"],
            ["policy_documents.id", "policy_documents.conversation_id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("document_id", "position", name="uq_policy_passage_position"),
    )
    op.create_index(
        "ix_policy_passages_scope", "policy_passages", ["conversation_id", "document_id"]
    )
    op.create_index(
        "ix_policy_passages_search", "policy_passages", ["search_vector"], postgresql_using="gin"
    )


def downgrade() -> None:
    op.drop_table("policy_passages")
    op.drop_constraint("uq_policy_document_conversation", "policy_documents", type_="unique")
    op.drop_column("policy_documents", "passage_count")
    op.drop_column("policy_documents", "page_count")
