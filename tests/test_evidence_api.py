import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Event

import pytest
from sqlalchemy.orm import Session

from api.llm.provider import Completion, ProviderError
from db.models import EvidenceSuggestion
from tests.test_api import ADJUSTER, MSG1
from tests.test_api import client as client

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs Postgres")
FIXTURE = Path(__file__).parent / "fixtures/claim_evidence.pdf"
SUGGESTIONS = [
    {
        "field": "estimated_amount_eur",
        "value": 1200,
        "page": 1,
        "quote": "Repair estimate: EUR 1200.00",
    },
    {
        "field": "incident_date",
        "value": "2026-10-25",
        "page": 2,
        "quote": "Incident date: 2026-10-25",
    },
]


def upload(client):
    conv = client.post("/api/conversations", json={"language": "en"}).json()
    response = client.post(
        f"/api/conversations/{conv['id']}/messages",
        data={"text": MSG1, "document_type": "repair_estimate"},
        files={"file": ("estimate.pdf", FIXTURE.read_bytes(), "application/pdf")},
    )
    assert response.status_code == 200 and "event: done" in response.text
    saved = client.get(f"/api/conversations/{conv['id']}").json()
    return conv, saved["attachments"][0]


def provider(monkeypatch, state, payload=None, fail_once=False):
    calls = []
    original = state.provider.complete

    def complete(*args, **kwargs):
        if kwargs.get("tag") != "evidence_extract":
            return original(*args, **kwargs)
        calls.append(kwargs)
        if fail_once and len(calls) == 1:
            raise ProviderError("temporary failure")
        return Completion(
            text=json.dumps({"suggestions": SUGGESTIONS if payload is None else payload})
        )

    monkeypatch.setattr(state.provider, "complete", complete)
    return calls


def endpoint(conv, attachment):
    return f"/api/conversations/{conv['id']}/attachments/{attachment['id']}/extract"


def test_pdf_suggestions_keep_confirmed_facts_and_sources_and_are_idempotent(client, monkeypatch):
    conv, attachment = upload(client)
    state = client.app.state.claimpilot
    before = client.get(f"/api/conversations/{conv['id']}").json()
    calls = provider(monkeypatch, state)
    result = client.post(endpoint(conv, attachment))
    assert result.status_code == 200
    data = result.json()
    assert data["processing_state"] == "ready" and data["page_count"] == 2
    assert len(data["suggestions"]) == 2
    assert [(s["field"], s["page"]) for s in data["suggestions"]] == [
        ("estimated_amount_eur", 1),
        ("incident_date", 2),
    ]
    assert all(
        s["source_document_id"] == attachment["id"]
        and s["source_name"] == "estimate.pdf"
        and s["status"] == "pending"
        for s in data["suggestions"]
    )
    assert client.post(endpoint(conv, attachment)).json() == data
    assert len(calls) == 1
    after = client.get(f"/api/conversations/{conv['id']}").json()
    for key in ["card", "status", "history", "messages"]:
        assert after[key] == before[key]
    assert after["attachments"][0] == data
    assert "path" not in data
    review = f"/api/claims/review-queue/{conv['claim_id']}"
    assert client.get(review).status_code == 401
    assert client.get(review, headers=ADJUSTER).json()["attachments"][0] == data
    other = client.post("/api/conversations", json={}).json()
    assert client.post(endpoint(other, attachment)).status_code == 404
    assert client.get(f"/api/conversations/{other['id']}").json()["attachments"] == []


@pytest.mark.parametrize(
    "payload,error",
    [
        ([{**SUGGESTIONS[0], "page": 2}], "unsupported_source_reference"),
        ([{**SUGGESTIONS[0], "field": "photos_attached", "value": True}], "extraction_failed"),
    ],
)
def test_invalid_model_suggestions_are_not_saved(client, monkeypatch, payload, error):
    conv, attachment = upload(client)
    provider(monkeypatch, client.app.state.claimpilot, payload)
    result = client.post(endpoint(conv, attachment)).json()
    assert result["processing_state"] == "failed" and result["error"] == error
    assert result["suggestions"] == []


def test_failed_extraction_can_retry_without_changing_facts(client, monkeypatch):
    conv, attachment = upload(client)
    calls = provider(monkeypatch, client.app.state.claimpilot, fail_once=True)
    assert client.post(endpoint(conv, attachment)).json()["processing_state"] == "failed"
    result = client.post(endpoint(conv, attachment)).json()
    assert result["processing_state"] == "ready" and len(result["suggestions"]) == 2
    assert len(calls) == 2


def test_evidence_extraction_rejects_unauthenticated_access(client, monkeypatch):
    conv, attachment = upload(client)
    state = client.app.state.claimpilot
    state.settings = replace(state.settings, demo_api_token="sample-access", allow_open_api=False)
    calls = provider(monkeypatch, state)
    assert client.post(endpoint(conv, attachment)).status_code == 401
    assert (
        client.post(
            endpoint(conv, attachment), headers={"Authorization": "Bearer incorrect"}
        ).status_code
        == 401
    )
    assert not calls
    assert (
        client.post(
            endpoint(conv, attachment), headers={"Authorization": "Bearer sample-access"}
        ).json()["processing_state"]
        == "ready"
    )


def test_concurrent_extractions_do_not_call_the_model_twice(client, monkeypatch):
    from api.routers import evidence

    conv, attachment = upload(client)
    calls = provider(monkeypatch, client.app.state.claimpilot)
    entered, release = Event(), Event()
    original = evidence.prepare_evidence_pdf

    def wait_for_release(path):
        entered.set()
        assert release.wait(10)
        return original(path)

    monkeypatch.setattr(evidence, "prepare_evidence_pdf", wait_for_release)
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(client.post, endpoint(conv, attachment))
        try:
            assert entered.wait(10)
            assert client.post(endpoint(conv, attachment)).status_code == 409
        finally:
            release.set()
        assert first.result().json()["processing_state"] == "ready"
    assert len(calls) == 1


def test_failed_suggestion_commit_is_not_ready_and_retry_is_atomic(client, monkeypatch):
    conv, attachment = upload(client)
    provider(monkeypatch, client.app.state.claimpilot)
    original = Session.commit
    failed = False

    def commit(session):
        nonlocal failed
        if not failed and any(isinstance(row, EvidenceSuggestion) for row in session.new):
            failed = True
            raise RuntimeError("simulated write failure")
        return original(session)

    monkeypatch.setattr(Session, "commit", commit)
    result = client.post(endpoint(conv, attachment)).json()
    assert result["processing_state"] == "failed" and result["suggestions"] == []
    result = client.post(endpoint(conv, attachment)).json()
    assert result["processing_state"] == "ready" and len(result["suggestions"]) == 2
