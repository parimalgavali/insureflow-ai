"""Remember customer message requests and their completed responses."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "message_operations",
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("user_text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(2), nullable=False),
        sa.Column("has_attachment", sa.Boolean(), nullable=False),
        sa.Column("base_message_count", sa.Integer(), nullable=False),
        sa.Column("response", postgresql.JSONB()),
    )


def downgrade() -> None:
    op.drop_table("message_operations")
