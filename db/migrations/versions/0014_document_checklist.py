"""Save requested documents and backfill existing claim requests without confirmation."""

import hashlib
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "claims",
        sa.Column("document_checklist", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    connection = op.get_bind()
    claims = sa.table(
        "claims",
        sa.column("id"),
        sa.column("card", postgresql.JSONB()),
        sa.column("created_at"),
        sa.column("document_checklist", postgresql.JSONB()),
    )
    for row in connection.execute(sa.select(claims.c.id, claims.c.card, claims.c.created_at)):
        items, keys = [], set()
        for label in (row.card or {}).get("missing_documents", []):
            label = label.strip()
            key = "assessment:" + hashlib.sha256(label.encode()).hexdigest()
            if label and key not in keys:
                keys.add(key)
                items.append(
                    {
                        "id": str(uuid.uuid4()),
                        "key": key,
                        "label": label,
                        "origin": "assessment",
                        "document_type": None,
                        "requested_at": row.created_at.isoformat(),
                        "linked": [],
                        "excluded": [],
                        "confirmed": [],
                        "confirmed_by": None,
                    }
                )
        connection.execute(
            claims.update().where(claims.c.id == row.id).values(document_checklist=items)
        )


def downgrade() -> None:
    op.drop_column("claims", "document_checklist")
