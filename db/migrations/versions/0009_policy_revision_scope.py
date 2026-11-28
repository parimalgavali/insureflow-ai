"""Prevent a policy revision from referencing another conversation's document."""

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "policy_documents_replaces_document_id_fkey", "policy_documents", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_policy_replacement_scope",
        "policy_documents",
        "policy_documents",
        ["replaces_document_id", "conversation_id"],
        ["id", "conversation_id"],
        deferrable=True,
        initially="DEFERRED",
    )


def downgrade() -> None:
    op.drop_constraint("fk_policy_replacement_scope", "policy_documents", type_="foreignkey")
    op.create_foreign_key(
        "policy_documents_replaces_document_id_fkey",
        "policy_documents",
        "policy_documents",
        ["replaces_document_id"],
        ["id"],
        ondelete="SET NULL",
    )
