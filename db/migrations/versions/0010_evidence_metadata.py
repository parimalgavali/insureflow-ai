"""Store verified media/document metadata without guessing types of legacy uploads."""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "attachments",
        sa.Column("media_type", sa.String(16), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "attachments",
        sa.Column("document_type", sa.String(32), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "attachments",
        sa.Column("processing_state", sa.String(32), nullable=False, server_default="unknown"),
    )
    op.add_column("attachments", sa.Column("error", sa.Text()))
    op.add_column(
        "message_operations",
        sa.Column("has_photo", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("message_operations", "has_photo")
    for column in ("error", "processing_state", "document_type", "media_type"):
        op.drop_column("attachments", column)
