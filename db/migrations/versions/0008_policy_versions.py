"""Retain policy versions with one current selection per conversation."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "policy_documents",
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "policy_documents", sa.Column("revision", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column(
        "policy_documents",
        sa.Column(
            "replaces_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("policy_documents.id", ondelete="SET NULL"),
        ),
    )
    op.drop_constraint("policy_documents_conversation_id_key", "policy_documents", type_="unique")
    op.create_index(
        "uq_policy_current_conversation",
        "policy_documents",
        ["conversation_id"],
        unique=True,
        postgresql_where=sa.text("is_current"),
    )


def downgrade() -> None:
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM policy_documents WHERE NOT is_current")):
        raise RuntimeError("Cannot downgrade while retained policy versions exist")
    op.drop_index("uq_policy_current_conversation", table_name="policy_documents")
    op.create_unique_constraint(
        "policy_documents_conversation_id_key", "policy_documents", ["conversation_id"]
    )
    op.drop_column("policy_documents", "replaces_document_id")
    op.drop_column("policy_documents", "revision")
    op.drop_column("policy_documents", "is_current")
