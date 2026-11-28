"""Recorded claim actions. Identity comes from access checks, never request bodies."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import select

from api.agent.schemas import FactChange
from db.models import Claim, ClaimEvent

EventKind = Literal[
    "submitted",
    "information_requested",
    "corrected",
    "assessment_refreshed",
    "assessment_refresh_failed",
    "review_completed",
    "evidence_accepted",
    "evidence_rejected",
    "evidence_replaced",
]


class HistoryEntry(BaseModel):
    id: int
    kind: EventKind
    actor: str
    decision: str | None
    note: str | None
    changes: list[FactChange]
    created_at: datetime


def history_out(claim: Claim) -> list[HistoryEntry]:
    return [
        HistoryEntry(
            id=event.id,
            kind=event.kind,
            actor=event.actor,
            decision=event.decision,
            note=event.note,
            changes=event.changes,
            created_at=event.created_at,
        )
        for event in claim.events
    ]


def record_event(
    session,
    claim: Claim,
    *,
    operation_id: str,
    kind: EventKind,
    actor: str,
    decision: str | None = None,
    note: str | None = None,
    changes: list[dict] | None = None,
    created_at: datetime | None = None,
) -> bool:
    exists = session.scalar(
        select(ClaimEvent.id).where(
            ClaimEvent.claim_id == claim.id,
            ClaimEvent.operation_id == operation_id,
            ClaimEvent.kind == kind,
        )
    )
    if exists is None:
        event = ClaimEvent(
            operation_id=operation_id,
            kind=kind,
            actor=actor,
            decision=decision,
            note=note,
            changes=changes or [],
        )
        if created_at is not None:
            event.created_at = created_at
        claim.events.append(event)
        return True
    return False


def record_review_events(session, claim: Claim, decision, result, operation_id: str) -> None:
    common = {
        "operation_id": operation_id,
        "actor": decision.reviewer,
        "decision": decision.decision,
        "note": decision.note,
    }
    if decision.decision == "request_info":
        record_event(session, claim, kind="information_requested", **common)
    elif decision.decision == "accept":
        record_event(session, claim, kind="review_completed", **common)
    else:
        changes = result.get("review_changes", result["card"].corrections)
        if decision.decision == "edit" and changes:
            record_event(
                session,
                claim,
                kind="corrected",
                changes=[c.model_dump(mode="json") for c in changes],
                **common,
            )
        if not result.get("reassessment_needed"):
            failed = result["card"].assessment_stale
            record_event(
                session,
                claim,
                kind="assessment_refresh_failed" if failed else "assessment_refreshed",
                **{**common, "note": result["card"].assessment_error if failed else decision.note},
            )
