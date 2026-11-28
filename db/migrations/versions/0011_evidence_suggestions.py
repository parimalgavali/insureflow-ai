"""Keep document suggestions separate from confirmed claim facts."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("attachments", sa.Column("page_count", sa.Integer()))
    op.create_table(
        "evidence_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "attachment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("attachments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("field", sa.String(40), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.UniqueConstraint("attachment_id", "position", name="uq_evidence_suggestion_position"),
    )
    op.create_index(
        "ix_evidence_suggestions_attachment_id", "evidence_suggestions", ["attachment_id"]
    )


def downgrade() -> None:
    op.drop_table("evidence_suggestions")
    op.drop_column("attachments", "page_count")
