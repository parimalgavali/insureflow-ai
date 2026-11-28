"""Saved requests plus current file links; an upload never confirms completeness."""

import copy
import hashlib
import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import select

from db.models import Attachment


class DocumentChecklistItem(BaseModel):
    id: uuid.UUID
    label: str
    document_type: str | None
    origin: Literal["assessment", "reviewer"]
    status: Literal["missing", "uploaded", "confirmed"]
    attachment_ids: list[uuid.UUID]
    confirmed_by: str | None = None


def inferred_document_type(label):
    text = label.casefold()
    groups = {
        "damage_photo": ("foto", "photo", "picture", "bilder"),
        "repair_estimate": ("kostenvoranschlag", "repair estimate", "workshop estimate"),
        "police_report": ("polizei", "police report"),
    }
    matches = [kind for kind, words in groups.items() if any(word in text for word in words)]
    return matches[0] if len(matches) == 1 else None


def effective_type(item):
    return item.get("document_type") or (
        inferred_document_type(item["label"]) if item["origin"] == "assessment" else None
    )


def new_request(key, label, origin, document_type=None, requested_at=None):
    return {
        "id": str(uuid.uuid4()),
        "key": key,
        "label": label,
        "origin": origin,
        "document_type": document_type,
        "requested_at": (requested_at or datetime.now(UTC)).isoformat(),
        "linked": [],
        "excluded": [],
        "confirmed": [],
        "confirmed_by": None,
    }


def sync_assessment_requests(claim):
    items = copy.deepcopy(claim.document_checklist or [])
    keys = {item["key"] for item in items}
    for label in (claim.card or {}).get("missing_documents", []):
        label = label.strip()
        if not label:
            continue
        key = "assessment:" + hashlib.sha256(label.encode()).hexdigest()
        if key not in keys:
            items.append(
                new_request(
                    key, label, "assessment", inferred_document_type(label), claim.created_at
                )
            )
            keys.add(key)
    claim.document_checklist = items


def add_reviewer_requests(claim, decision, action_id):
    items = copy.deepcopy(claim.document_checklist or [])
    requests = [request.model_dump() for request in decision.requested_documents]
    for position, request in enumerate(requests):
        key = f"review:{action_id}:{position}"
        if not any(item["key"] == key for item in items):
            items.append(new_request(key, request["label"], "reviewer", request["document_type"]))
    claim.document_checklist = items


def checklist_out(session, claim):
    files = {
        str(row.id): row
        for row in session.scalars(
            select(Attachment).where(Attachment.conversation_id == claim.conversation_id)
        )
    }
    replacements = {
        str(row.replaces_attachment_id): str(row.id)
        for row in files.values()
        if row.replaces_attachment_id
    }

    def current_id(file_id):
        seen = set()
        while file_id in replacements and file_id not in seen:
            seen.add(file_id)
            file_id = replacements[file_id]
        row = files.get(file_id)
        return (
            file_id
            if row is not None and row.is_current and row.media_type in ("pdf", "image")
            else None
        )

    output = []
    for item in claim.document_checklist or []:
        kind = effective_type(item)
        requested = datetime.fromisoformat(item["requested_at"])
        linked = {current_id(file_id) for file_id in item["linked"]}
        excluded = {current_id(file_id) for file_id in item["excluded"]}
        if kind:
            linked.update(
                str(row.id)
                for row in files.values()
                if row.is_current
                and row.media_type in ("pdf", "image")
                and row.document_type == kind
                and (kind != "damage_photo" or row.media_type == "image")
                and (item["origin"] == "assessment" or row.created_at >= requested)
            )
        linked = sorted(linked - excluded - {None})
        confirmed = bool(linked) and linked == sorted(item["confirmed"])
        output.append(
            DocumentChecklistItem(
                id=item["id"],
                label=item["label"],
                document_type=kind,
                origin=item["origin"],
                status="confirmed" if confirmed else "uploaded" if linked else "missing",
                attachment_ids=linked,
                confirmed_by=item.get("confirmed_by") if confirmed else None,
            )
        )
    return output
