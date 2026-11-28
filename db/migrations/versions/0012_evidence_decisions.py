"""Keep the confirmed baseline for recoverable document decisions."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("evidence_suggestions", sa.Column("expected_value", postgresql.JSONB()))


def downgrade() -> None:
    op.drop_column("evidence_suggestions", "expected_value")
