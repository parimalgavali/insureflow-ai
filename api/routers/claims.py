from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from api.agent.graph import resume_review, submit_for_review, thread_config
from api.agent.schemas import ClaimCard, ReviewDecision, ReviewRequest
from api.history import HistoryEntry, history_out, record_event, record_review_events
from api.security import get_state, require_adjuster, require_token
from db.models import Claim, Message

router = APIRouter(prefix="/api/claims", tags=["claims"], dependencies=[Depends(require_token)])


class ClaimOut(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    status: str
    card: ClaimCard | None
    submitted_at: datetime | None
    history: list[HistoryEntry]


def _out(claim: Claim) -> ClaimOut:
    return ClaimOut(
        id=claim.id,
        conversation_id=claim.conversation_id,
        status=claim.status,
        card=ClaimCard.model_validate(claim.card) if claim.card else None,
        submitted_at=claim.submitted_at,
        history=history_out(claim),
    )


class QueueItem(BaseModel):
    id: uuid.UUID
    submitted_at: datetime | None
    event_type: str
    location: str | None


class ReviewQueue(BaseModel):
    items: list[QueueItem]
    has_more: bool


@router.get("/review-queue", response_model=ReviewQueue)
def review_queue(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    reviewer: str = Depends(require_adjuster),
    state=Depends(get_state),
) -> ReviewQueue:
    with state.session() as session:
        claims = list(
            session.scalars(
                select(Claim)
                .where(Claim.status == "awaiting_review")
                .order_by(Claim.submitted_at.asc().nullslast(), Claim.created_at, Claim.id)
                .offset(offset)
                .limit(limit + 1)
            )
        )
        return ReviewQueue(
            items=[
                QueueItem(
                    id=claim.id,
                    submitted_at=claim.submitted_at,
                    event_type=(claim.card or {}).get("facts", {}).get("event_type", "unknown"),
                    location=(claim.card or {}).get("facts", {}).get("location"),
                )
                for claim in claims[:limit]
            ],
            has_more=len(claims) > limit,
        )


@router.get("/review-queue/{claim_id}", response_model=ClaimOut)
def reviewer_claim(
    claim_id: uuid.UUID,
    reviewer: str = Depends(require_adjuster),
    state=Depends(get_state),
) -> ClaimOut:
    return get_claim(claim_id, state)


@router.get("/{claim_id}", response_model=ClaimOut)
def get_claim(claim_id: uuid.UUID, state=Depends(get_state)) -> ClaimOut:
    with state.session() as session:
        claim = session.get(Claim, claim_id)
        if claim is None:
            raise HTTPException(404, "claim not found")
        return _out(claim)


@router.post("/{claim_id}/submit", response_model=ClaimOut)
def submit_claim(claim_id: uuid.UUID, state=Depends(get_state)) -> ClaimOut:
    """Submit once; a retry returns the saved claim without recording a review."""
    with state.session() as session:
        # Serialize competing submissions for the same claim across API workers.
        claim = session.scalar(select(Claim).where(Claim.id == claim_id).with_for_update())
        if claim is None:
            raise HTTPException(404, "claim not found")
        if claim.status in ("awaiting_review", "reviewed"):
            return _out(claim)
        if claim.status != "assessed":
            raise HTTPException(409, "claim is not ready to submit")
        try:
            result = submit_for_review(state.graph, str(claim.conversation_id))
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        claim.card = result["card"].model_dump(mode="json")
        claim.status = result["status"]
        claim.submitted_at = datetime.now(UTC)
        claim.conversation.status = result["status"]
        record_event(
            session,
            claim,
            operation_id=result.get("submission_id") or uuid.uuid4().hex,
            kind="submitted",
            actor="customer",
            created_at=claim.submitted_at,
        )
        session.commit()
        return _out(claim)


@router.post("/{claim_id}/review", response_model=ClaimOut)
def review_claim(
    claim_id: uuid.UUID,
    body: ReviewRequest,
    reviewer: str = Depends(require_adjuster),
    state=Depends(get_state),
) -> ClaimOut:
    """Record an authorized review or reopen the claim for more information."""
    decision = ReviewDecision(**body.model_dump(), reviewer=reviewer)
    with state.session() as session:
        claim = session.scalar(select(Claim).where(Claim.id == claim_id).with_for_update())
        if claim is None:
            raise HTTPException(404, "claim not found")
        if claim.status != "awaiting_review":
            raise HTTPException(409, f"claim is {claim.status}, not awaiting_review")
        thread = str(claim.conversation_id)
        snapshot = state.graph.get_state(thread_config(thread))
        if decision.decision == "accept" and (
            (claim.card or {}).get("assessment_stale")
            or getattr(snapshot.values.get("card"), "assessment_stale", False)
        ):
            raise HTTPException(409, "refresh the out-of-date assessment before completing review")
        if (
            (
                decision.decision == "edit"
                or (
                    decision.decision == "reassess"
                    and not getattr(snapshot.values.get("card"), "assessment_stale", True)
                )
            )
            and snapshot.values.get("status") == "awaiting_review"
            and snapshot.values.get("review") == decision
        ):
            # Recover saved corrections or a successful recheck without another model call.
            result = snapshot.values
        elif snapshot.next == ("reassess",) and decision.decision == "reassess":
            result = state.graph.invoke(None, thread_config(thread))
        elif snapshot.next == ("human_review",):
            result = resume_review(state.graph, thread, decision)
        elif (
            snapshot.values.get("status") in ("information_needed", "reviewed")
            and snapshot.values.get("review") == decision
        ):
            # Checkpoints and claim rows commit separately. Recover the exact saved
            # decision after a failed row commit without invoking the graph again.
            result = snapshot.values
        else:
            raise HTTPException(409, "agent is not waiting for review on this conversation")
        claim.card = result["card"].model_dump(mode="json")
        claim.status = result["status"]
        claim.conversation.status = result["status"]
        if decision.decision == "request_info":
            claim.conversation.messages.append(
                Message(role="assistant", content=result["messages"][-1].content)
            )
        operation_id = result.get("review_action_id") or (
            "legacy-" + str(snapshot.config["configurable"]["checkpoint_id"])
        )
        record_review_events(session, claim, decision, result, operation_id)
        session.commit()
        return _out(claim)


@router.get("/{claim_id}/history", response_model=list[HistoryEntry])
def get_history(claim_id: uuid.UUID, state=Depends(get_state)) -> list[HistoryEntry]:
    with state.session() as session:
        claim = session.get(Claim, claim_id)
        if claim is None:
            raise HTTPException(404, "claim not found")
        return history_out(claim)
