"""Persist ordered claim actions without inventing missing historical activity."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "claim_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "claim_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("claims.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("operation_id", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("actor", sa.String(32), nullable=False),
        sa.Column("decision", sa.String(32)),
        sa.Column("note", sa.Text()),
        sa.Column("changes", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("claim_id", "operation_id", "kind", name="uq_claim_event_operation"),
    )
    op.create_index("ix_claim_events_claim_id", "claim_events", ["claim_id"])


def downgrade() -> None:
    op.drop_index("ix_claim_events_claim_id", table_name="claim_events")
    op.drop_table("claim_events")
