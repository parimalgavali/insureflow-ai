from __future__ import annotations

import copy
import uuid
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import object_session

from api.agent.graph import correct_customer_facts, resume_review, submit_for_review, thread_config
from api.agent.required_facts import missing_facts
from api.agent.schemas import ClaimCard, CustomerCorrection, ReviewDecision, ReviewRequest
from api.checklist import (
    DocumentChecklistItem,
    add_reviewer_requests,
    checklist_out,
    sync_assessment_requests,
)
from api.evidence import AttachmentOut, attachments_out
from api.evidence_decisions import require_no_pending_evidence
from api.history import HistoryEntry, history_out, record_event, record_review_events
from api.policy_coverage import coverage_source_changed, current_coverage_card
from api.security import get_state, require_adjuster, require_token
from db.models import (
    Attachment,
    Claim,
    Conversation,
    EvidenceSuggestion,
    Message,
    MessageOperation,
    PolicyDocument,
)

router = APIRouter(prefix="/api/claims", tags=["claims"], dependencies=[Depends(require_token)])


class ClaimOut(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    status: str
    card: ClaimCard | None
    submitted_at: datetime | None
    history: list[HistoryEntry]
    missing: list[str]
    attachments: list[AttachmentOut] = Field(default_factory=list)
    document_checklist: list[DocumentChecklistItem] = Field(default_factory=list)


def _out(claim: Claim) -> ClaimOut:
    card = ClaimCard.model_validate(claim.card) if claim.card else None
    if card is not None:
        card = current_coverage_card(
            object_session(claim), card, claim.conversation_id, claim.conversation.language
        )
    return ClaimOut(
        id=claim.id,
        conversation_id=claim.conversation_id,
        status=claim.status,
        card=card,
        attachments=attachments_out(object_session(claim), claim.conversation_id),
        document_checklist=checklist_out(object_session(claim), claim),
        submitted_at=claim.submitted_at,
        history=history_out(claim),
        missing=missing_facts(ClaimCard.model_validate(claim.card).facts) if claim.card else [],
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


def _require_finished_message(session, claim, allowed_suggestion_id=None):
    # Same conversation row lock as message creation: no edit can slip between
    # checking for an unfinished message and reserving its operation.
    session.scalar(
        select(Conversation.id).where(Conversation.id == claim.conversation_id).with_for_update()
    )
    pending = session.scalar(
        select(MessageOperation.id)
        .where(
            MessageOperation.conversation_id == claim.conversation_id,
            MessageOperation.response.is_(None),
        )
        .limit(1)
    )
    if pending:
        raise HTTPException(409, "retry the unfinished message before changing this claim")
    require_no_pending_evidence(session, claim.conversation_id, allowed_suggestion_id)
    policy = session.scalar(
        select(PolicyDocument)
        .where(
            PolicyDocument.conversation_id == claim.conversation_id,
            PolicyDocument.is_current.is_(True),
        )
        .with_for_update()
    )
    if policy is not None and policy.status == "processing":
        raise HTTPException(409, "wait for policy text preparation before changing this claim")


@router.post("/{claim_id}/submit", response_model=ClaimOut)
def submit_claim(claim_id: uuid.UUID, state=Depends(get_state)) -> ClaimOut:
    """Submit once; a retry returns the saved claim without recording a review."""
    with state.session() as session:
        # Serialize competing submissions for the same claim across API workers.
        claim = session.scalar(select(Claim).where(Claim.id == claim_id).with_for_update())
        if claim is None:
            raise HTTPException(404, "claim not found")
        _require_finished_message(session, claim)
        if claim.status in ("awaiting_review", "reviewed"):
            return _out(claim)
        if claim.status != "assessed":
            raise HTTPException(409, "claim is not ready to submit")
        if _out(claim).card.assessment_stale:
            raise HTTPException(409, "refresh the assessment before submitting")
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


def _customer_action(claim_id: uuid.UUID, patch: dict, state, *, refresh: bool = False) -> ClaimOut:
    with state.session() as session:
        claim = session.scalar(select(Claim).where(Claim.id == claim_id).with_for_update())
        if claim is None:
            raise HTTPException(404, "claim not found")
        _require_finished_message(session, claim)
        if claim.status not in ("collecting", "assessed", "information_needed"):
            raise HTTPException(409, "customer corrections are only available before submission")
        _apply_customer_action(session, claim, patch, state, refresh=refresh)
        session.commit()
        return _out(claim)


def _apply_customer_action(session, claim, patch, state, *, refresh=False, action_id=None):
    try:
        result = correct_customer_facts(
            state.graph, str(claim.conversation_id), patch, refresh=refresh, action_id=action_id
        )
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    card = result.get("card") or ClaimCard(
        facts=result["facts"], policy=result["policy"], status=result["status"]
    )
    card = current_coverage_card(session, card, claim.conversation_id, claim.conversation.language)
    claim.card = card.model_dump(mode="json")
    sync_assessment_requests(claim)
    claim.status = card.status
    claim.conversation.status = card.status
    operation_id = result.get("customer_action_id")
    if operation_id:
        changes = result.get("customer_changes", [])
        if changes and record_event(
            session,
            claim,
            operation_id=operation_id,
            kind="corrected",
            actor="customer",
            decision="edit",
            changes=[c.model_dump(mode="json") for c in changes],
        ):
            note = result.get("customer_correction_message")
            if note:
                claim.conversation.messages.append(Message(role="user", content=note))
        if result["status"] == "assessed" and not result.get("reassessment_needed"):
            failed = card.assessment_stale
            if record_event(
                session,
                claim,
                operation_id=operation_id,
                kind="assessment_refresh_failed" if failed else "assessment_refreshed",
                actor="customer",
                decision="reassess" if refresh else "edit",
                note=card.assessment_error if failed else None,
            ):
                note = result.get("customer_assessment_message")
                if note:
                    claim.conversation.messages.append(Message(role="assistant", content=note))


@router.patch("/{claim_id}/facts", response_model=ClaimOut)
def correct_facts(
    claim_id: uuid.UUID, body: CustomerCorrection, state=Depends(get_state)
) -> ClaimOut:
    return _customer_action(claim_id, body.facts_patch, state)


@router.post("/{claim_id}/facts/refresh", response_model=ClaimOut)
def refresh_customer_assessment(claim_id: uuid.UUID, state=Depends(get_state)) -> ClaimOut:
    return _customer_action(claim_id, {}, state, refresh=True)


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
        _require_finished_message(session, claim)
        if claim.status != "awaiting_review":
            raise HTTPException(409, f"claim is {claim.status}, not awaiting_review")
        thread = str(claim.conversation_id)
        snapshot = state.graph.get_state(thread_config(thread))
        if decision.decision == "accept" and (
            _out(claim).card.assessment_stale
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
            and not coverage_source_changed(session, snapshot.values["card"], claim.conversation_id)
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
        sync_assessment_requests(claim)
        if decision.decision == "request_info":
            add_reviewer_requests(claim, decision, operation_id)
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


class EvidenceDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    decision: Literal["accept", "reject"]
    expected_current: str | float | bool | None
    replace_existing: bool = False


def _same_value(first, second):
    if isinstance(first, bool) or isinstance(second, bool):
        return type(first) is type(second) and first == second
    return first == second


def _load_suggestion(session, claim, suggestion_id):
    suggestion = session.scalar(
        select(EvidenceSuggestion)
        .join(Attachment)
        .where(
            EvidenceSuggestion.id == suggestion_id,
            Attachment.conversation_id == claim.conversation_id,
            Attachment.processing_state == "ready",
            Attachment.is_current.is_(True),
        )
        .with_for_update(of=EvidenceSuggestion)
    )
    if suggestion is None:
        raise HTTPException(404, "suggestion not found")
    return suggestion


def _record_evidence_decision(session, claim, suggestion, decision):
    attachment = session.get(Attachment, suggestion.attachment_id)
    record_event(
        session,
        claim,
        operation_id="evidence-" + suggestion.id.hex,
        kind="evidence_accepted" if decision == "accept" else "evidence_rejected",
        actor="customer",
        decision=decision,
        note=f"{attachment.filename}, page {suggestion.page}",
    )


@router.post("/{claim_id}/evidence-suggestions/{suggestion_id}/decision", response_model=ClaimOut)
def decide_evidence_suggestion(
    claim_id: uuid.UUID, suggestion_id: uuid.UUID, body: EvidenceDecision, state=Depends(get_state)
) -> ClaimOut:
    # Reserve the decision durably before changing graph checkpoints. A stopped
    # request can finish this exact confirmation without allowing an intervening edit.
    with state.session() as session:
        claim = session.scalar(select(Claim).where(Claim.id == claim_id).with_for_update())
        if claim is None:
            raise HTTPException(404, "claim not found")
        suggestion = _load_suggestion(session, claim, suggestion_id)
        final_status = "accepted" if body.decision == "accept" else "rejected"
        if suggestion.status in ("accepted", "rejected"):
            if suggestion.status != final_status:
                raise HTTPException(409, "suggestion already decided")
            return _out(claim)  # Replays never reapply an old fact after a later edit.
        _require_finished_message(session, claim, suggestion_id)
        if claim.status not in ("collecting", "assessed", "information_needed"):
            raise HTTPException(409, "document confirmation is only available before submission")
        if suggestion.status == "applying":
            if body.decision != "accept" or not _same_value(
                body.expected_current, suggestion.expected_value
            ):
                raise HTTPException(409, "finish the original document confirmation")
        elif suggestion.status == "pending":
            if body.decision == "reject":
                suggestion.status = "rejected"
                _record_evidence_decision(session, claim, suggestion, "reject")
                session.commit()
                return _out(claim)
            if not claim.card:
                raise HTTPException(409, "describe the incident before confirming document facts")
            facts = ClaimCard.model_validate(claim.card).facts
            current = getattr(facts, suggestion.field)
            if not _same_value(current, body.expected_current):
                raise HTTPException(409, {"code": "claim_fact_changed", "field": suggestion.field})
            if (
                current not in (None, "unknown")
                and not _same_value(current, suggestion.value)
                and not body.replace_existing
            ):
                raise HTTPException(409, "confirm replacing the existing claim value")
            snapshot = state.graph.get_state(thread_config(str(claim.conversation_id)))
            if snapshot.values.get("facts") != facts:
                raise HTTPException(
                    409, "finish the pending claim update before confirming a document"
                )
            suggestion.expected_value = current
            suggestion.status = "applying"
            session.commit()
        else:
            raise HTTPException(409, "suggestion cannot be confirmed")
    with state.session() as session:
        claim = session.scalar(select(Claim).where(Claim.id == claim_id).with_for_update())
        if claim is None:
            raise HTTPException(404, "claim not found")
        suggestion = _load_suggestion(session, claim, suggestion_id)
        if suggestion.status == "accepted":
            return _out(claim)
        _require_finished_message(session, claim, suggestion_id)
        _apply_customer_action(
            session,
            claim,
            {suggestion.field: suggestion.value},
            state,
            action_id="evidence-" + suggestion.id.hex,
        )
        suggestion.status = "accepted"
        _record_evidence_decision(session, claim, suggestion, "accept")
        session.commit()
        return _out(claim)


class ChecklistConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attachment_ids: list[uuid.UUID] = Field(max_length=100)
    confirmed: bool = True


def _saved_checklist_item(claim, item_id):
    items = copy.deepcopy(claim.document_checklist or [])
    item = next((item for item in items if item["id"] == str(item_id)), None)
    if item is None:
        raise HTTPException(404, "document request not found")
    return items, item


@router.put("/{claim_id}/documents/{item_id}/attachments/{attachment_id}", response_model=ClaimOut)
def link_checklist_file(
    claim_id: uuid.UUID, item_id: uuid.UUID, attachment_id: uuid.UUID, state=Depends(get_state)
):
    return _set_checklist_link(claim_id, item_id, attachment_id, True, state)


@router.delete(
    "/{claim_id}/documents/{item_id}/attachments/{attachment_id}", response_model=ClaimOut
)
def unlink_checklist_file(
    claim_id: uuid.UUID, item_id: uuid.UUID, attachment_id: uuid.UUID, state=Depends(get_state)
):
    return _set_checklist_link(claim_id, item_id, attachment_id, False, state)


def _set_checklist_link(claim_id, item_id, attachment_id, linked, state):
    from api.checklist import effective_type

    with state.session() as session:
        claim = session.scalar(select(Claim).where(Claim.id == claim_id).with_for_update())
        if claim is None:
            raise HTTPException(404, "claim not found")
        _require_finished_message(session, claim)
        if claim.status not in ("collecting", "assessed", "information_needed"):
            raise HTTPException(409, "link documents before submission")
        items, item = _saved_checklist_item(claim, item_id)
        attachment = session.scalar(
            select(Attachment).where(
                Attachment.id == attachment_id,
                Attachment.conversation_id == claim.conversation_id,
                Attachment.is_current.is_(True),
            )
        )
        if attachment is None:
            raise HTTPException(404, "current attachment not found")
        kind = effective_type(item)
        if (
            attachment.media_type not in ("pdf", "image")
            or (
                kind
                and attachment.document_type != kind
                and not (kind != "damage_photo" and attachment.document_type == "other_document")
            )
            or (kind == "damage_photo" and attachment.media_type != "image")
        ):
            raise HTTPException(422, "choose a verified attachment of the requested type")
        file_id = str(attachment_id)
        family = {file_id}
        parent = attachment
        while parent.replaces_attachment_id:
            family.add(str(parent.replaces_attachment_id))
            parent = session.get(Attachment, parent.replaces_attachment_id)
        if (
            linked
            and family.intersection(item["linked"])
            and not family.intersection(item["excluded"])
        ):
            return _out(claim)
        if (
            not linked
            and family.intersection(item["excluded"])
            and not family.intersection(item["linked"])
        ):
            return _out(claim)
        item["linked"] = sorted((set(item["linked"]) - family) | ({file_id} if linked else set()))
        item["excluded"] = sorted(
            (set(item["excluded"]) - family) | (set() if linked else {file_id})
        )
        item["confirmed"], item["confirmed_by"] = [], None
        claim.document_checklist = items
        record_event(
            session,
            claim,
            operation_id=uuid.uuid4().hex,
            kind="document_linked" if linked else "document_unlinked",
            actor="customer",
            note=f"{item['label']}: {attachment.filename}",
        )
        session.commit()
        return _out(claim)


@router.post("/{claim_id}/documents/{item_id}/confirmation", response_model=ClaimOut)
def confirm_checklist_document(
    claim_id: uuid.UUID,
    item_id: uuid.UUID,
    body: ChecklistConfirmation,
    reviewer: str = Depends(require_adjuster),
    state=Depends(get_state),
):
    with state.session() as session:
        claim = session.scalar(select(Claim).where(Claim.id == claim_id).with_for_update())
        if claim is None:
            raise HTTPException(404, "claim not found")
        _require_finished_message(session, claim)
        if claim.status != "awaiting_review":
            raise HTTPException(409, "check documents while the claim awaits review")
        items, item = _saved_checklist_item(claim, item_id)
        current = next(row for row in checklist_out(session, claim) if row.id == item_id)
        files = sorted(str(file_id) for file_id in current.attachment_ids)
        if files != sorted(set(str(file_id) for file_id in body.attachment_ids)):
            raise HTTPException(409, "document copies changed; check the current files")
        if body.confirmed and not files:
            raise HTTPException(422, "link the requested document before confirming it")
        expected = files if body.confirmed else []
        if sorted(item["confirmed"]) == expected:
            return _out(claim)
        item["confirmed"], item["confirmed_by"] = expected, reviewer if body.confirmed else None
        claim.document_checklist = items
        copies = list(
            session.scalars(
                select(Attachment)
                .where(Attachment.id.in_([uuid.UUID(file_id) for file_id in files]))
                .order_by(Attachment.created_at, Attachment.id)
            )
        )
        copy_names = "; ".join(f"{row.filename} (version {row.revision})" for row in copies)
        record_event(
            session,
            claim,
            operation_id=uuid.uuid4().hex,
            kind="documents_confirmed" if body.confirmed else "documents_confirmation_cleared",
            actor=reviewer,
            note=f"{item['label']}: {copy_names}",
        )
        session.commit()
        return _out(claim)
