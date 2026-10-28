from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.agent.graph import resume_review, thread_config
from api.agent.schemas import ClaimCard, ReviewDecision
from api.security import get_state, require_token
from db.models import Claim

router = APIRouter(prefix="/api/claims", tags=["claims"], dependencies=[Depends(require_token)])


class ClaimOut(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    status: str
    card: ClaimCard | None


def _out(claim: Claim) -> ClaimOut:
    return ClaimOut(
        id=claim.id,
        conversation_id=claim.conversation_id,
        status=claim.status,
        card=ClaimCard.model_validate(claim.card) if claim.card else None,
    )


@router.get("/{claim_id}", response_model=ClaimOut)
def get_claim(claim_id: uuid.UUID, state=Depends(get_state)) -> ClaimOut:
    with state.session() as session:
        claim = session.get(Claim, claim_id)
        if claim is None:
            raise HTTPException(404, "claim not found")
        return _out(claim)


@router.post("/{claim_id}/review", response_model=ClaimOut)
def review_claim(
    claim_id: uuid.UUID, decision: ReviewDecision, state=Depends(get_state)
) -> ClaimOut:
    """Resume the interrupted graph with the reviewer's decision and persist the reviewed card."""
    with state.session() as session:
        claim = session.get(Claim, claim_id)
        if claim is None:
            raise HTTPException(404, "claim not found")
        if claim.status != "awaiting_review":
            raise HTTPException(409, f"claim is {claim.status}, not awaiting_review")
        thread = str(claim.conversation_id)
    snapshot = state.graph.get_state(thread_config(thread))
    if not snapshot.next or "human_review" not in snapshot.next:
        raise HTTPException(409, "agent is not waiting for review on this conversation")
    result = resume_review(state.graph, thread, decision)
    with state.session() as session:
        claim = session.get(Claim, claim_id)
        claim.card = result["card"].model_dump(mode="json")
        claim.status = result["status"]
        claim.conversation.status = result["status"]
        session.commit()
        return _out(claim)
