"""Retain earlier evidence versions and scope replacement links to one claim."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "attachments",
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "attachments", sa.Column("revision", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column("attachments", sa.Column("replaces_attachment_id", postgresql.UUID(as_uuid=True)))
    op.add_column("attachments", sa.Column("content_hash", sa.String(64)))
    op.create_unique_constraint(
        "uq_attachment_conversation", "attachments", ["id", "conversation_id"]
    )
    op.create_unique_constraint(
        "uq_attachment_replacement", "attachments", ["replaces_attachment_id"]
    )
    op.create_foreign_key(
        "fk_attachment_replacement_scope",
        "attachments",
        "attachments",
        ["replaces_attachment_id", "conversation_id"],
        ["id", "conversation_id"],
        deferrable=True,
        initially="DEFERRED",
    )


def downgrade() -> None:
    op.drop_constraint("fk_attachment_replacement_scope", "attachments", type_="foreignkey")
    op.drop_constraint("uq_attachment_replacement", "attachments", type_="unique")
    op.drop_constraint("uq_attachment_conversation", "attachments", type_="unique")
    for column in ("content_hash", "replaces_attachment_id", "revision", "is_current"):
        op.drop_column("attachments", column)
