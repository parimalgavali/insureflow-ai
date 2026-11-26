"""Record the actual customer submission time for the reviewer queue."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Earlier claims have no known submission time; do not invent one from created_at.
    op.add_column("claims", sa.Column("submitted_at", sa.DateTime(timezone=True)))
    op.create_index("ix_claims_status_submitted_at", "claims", ["status", "submitted_at"])


def downgrade() -> None:
    op.drop_index("ix_claims_status_submitted_at", table_name="claims")
    op.drop_column("claims", "submitted_at")
