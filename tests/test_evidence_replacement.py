import os
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from threading import Event

import pytest
from pypdf import PdfReader, PdfWriter
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models import Attachment, Conversation
from tests.test_api import MSG1
from tests.test_evidence_api import client as client
from tests.test_evidence_api import endpoint, provider, upload

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs Postgres")
FIXTURE = Path(__file__).parent / "fixtures/claim_evidence.pdf"


def pdf_bytes(kind):
    if kind == "scan":
        return (Path(__file__).parent / "fixtures/unreadable_claim.pdf").read_bytes()
    writer = PdfWriter()
    if kind == "readable":
        writer.append(PdfReader(FIXTURE))
        writer.add_metadata({"/Title": "Clearer sample copy"})
    else:
        writer.add_blank_page(width=100, height=100)
        if kind == "encrypted":
            writer.encrypt("sample-password")
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def replace_url(conv, attachment):
    return f"/api/conversations/{conv['id']}/attachments/{attachment['id']}"


def replace_file(client, conv, attachment, data=None, filename="clear.pdf"):
    return client.put(
        replace_url(conv, attachment),
        files={"file": (filename, data or pdf_bytes("readable"), "application/pdf")},
    )


@pytest.mark.parametrize("kind,code", [("blank", "empty_pdf"), ("scan", "no_selectable_text")])
def test_unreadable_pdf_produces_no_suggestions_and_keeps_the_claim(
    client, monkeypatch, kind, code
):
    conv = client.post("/api/conversations", json={}).json()
    client.post(
        f"/api/conversations/{conv['id']}/messages",
        data={"text": MSG1},
        files={"file": ("unreadable.pdf", pdf_bytes(kind), "application/pdf")},
    )
    before = client.get(f"/api/conversations/{conv['id']}").json()
    calls = provider(monkeypatch, client.app.state.claimpilot)
    result = client.post(endpoint(conv, before["attachments"][0])).json()
    assert result["processing_state"] == "failed" and result["error"] == code
    assert result["suggestions"] == [] and not calls
    after = client.get(f"/api/conversations/{conv['id']}").json()
    assert before["card"] == after["card"] and before["messages"] == after["messages"]
    replacement = replace_file(client, conv, result).json()
    assert replacement["is_current"] and replacement["processing_state"] == "stored"
    read = client.post(endpoint(conv, replacement)).json()
    assert read["processing_state"] == "ready" and len(read["suggestions"]) == 2
    assert len(calls) == 1


@pytest.mark.parametrize(
    "data,code",
    [
        (b"", "empty_file"),
        (b"%PDF-broken", "damaged_pdf"),
        (pdf_bytes("encrypted"), "encrypted_pdf"),
    ],
)
def test_rejected_pdf_upload_explains_the_problem_without_a_saved_turn(client, data, code):
    conv = client.post("/api/conversations", json={}).json()
    result = client.post(
        f"/api/conversations/{conv['id']}/messages",
        data={"text": MSG1},
        files={"file": ("report.pdf", data, "application/pdf")},
    )
    assert result.status_code == 422 and result.json()["detail"] == code
    restored = client.get(f"/api/conversations/{conv['id']}").json()
    assert len(restored["messages"]) == 1 and restored["attachments"] == []


def test_replacement_retains_versions_decisions_and_facts_but_old_suggestions_are_read_only(
    client, monkeypatch
):
    conv, attachment = upload(client)
    provider(monkeypatch, client.app.state.claimpilot)
    read = client.post(endpoint(conv, attachment)).json()
    first, second = read["suggestions"]
    url = f"/api/claims/{conv['claim_id']}/evidence-suggestions/{first['id']}/decision"
    client.post(url, json={"decision": "accept", "expected_current": None})
    before = client.get(f"/api/conversations/{conv['id']}").json()
    response = replace_file(client, conv, attachment)
    assert response.status_code == 200
    replacement = response.json()
    assert (
        replacement["revision"] == 2 and replacement["replaces_attachment_id"] == attachment["id"]
    )
    assert replacement["suggestions"] == [] and replacement["is_current"]
    after = client.get(f"/api/conversations/{conv['id']}").json()
    assert after["card"] == before["card"] and after["messages"] == before["messages"]
    assert [s["status"] for s in after["attachments"][0]["suggestions"]] == [
        "accepted",
        "superseded",
    ]
    assert not after["attachments"][0]["is_current"]
    for suggestion in [first, second]:
        assert (
            client.post(
                f"/api/claims/{conv['claim_id']}/evidence-suggestions/{suggestion['id']}/decision",
                json={"decision": "accept", "expected_current": None},
            ).status_code
            == 404
        )
    assert client.post(endpoint(conv, attachment)).status_code == 409
    assert replace_file(client, conv, attachment).json() == replacement  # Lost-response retry.
    assert (
        sum(
            e["kind"] == "evidence_replaced"
            for e in client.get(f"/api/conversations/{conv['id']}").json()["history"]
        )
        == 1
    )
    other = client.post("/api/conversations", json={}).json()
    assert replace_file(client, other, attachment).status_code == 404


def test_failed_replacement_preserves_original_file_and_metadata(client, monkeypatch):
    conv, attachment = upload(client)
    state = client.app.state.claimpilot
    before_files = set(state.settings.upload_dir.rglob("*"))
    original = Session.commit

    def commit(session):
        if any(
            isinstance(row, Attachment) and row.replaces_attachment_id
            for row in session.identity_map.values()
        ):
            raise RuntimeError("simulated replacement write failure")
        return original(session)

    monkeypatch.setattr(Session, "commit", commit)
    with pytest.raises(RuntimeError, match="replacement write"):
        replace_file(client, conv, attachment)
    restored = client.get(f"/api/conversations/{conv['id']}").json()
    assert len(restored["attachments"]) == 1 and restored["attachments"][0]["is_current"]
    assert restored["history"] == []
    assert set(state.settings.upload_dir.rglob("*")) == before_files


def test_replacement_waits_for_live_reading_and_allows_recovery_afterward(client, monkeypatch):
    from api.routers import evidence

    conv, attachment = upload(client)
    provider(monkeypatch, client.app.state.claimpilot)
    entered, release = Event(), Event()
    original = evidence.prepare_evidence_pdf

    def wait_for_release(path):
        entered.set()
        assert release.wait(10)
        return original(path)

    monkeypatch.setattr(evidence, "prepare_evidence_pdf", wait_for_release)
    with ThreadPoolExecutor(max_workers=1) as pool:
        reading = pool.submit(client.post, endpoint(conv, attachment))
        try:
            assert entered.wait(10)
            assert replace_file(client, conv, attachment).status_code == 409
        finally:
            release.set()
        assert reading.result().json()["processing_state"] == "ready"
    assert replace_file(client, conv, attachment).status_code == 200


def test_database_rejects_cross_claim_replacement_and_allows_scoped_deletion(client):
    import uuid

    conv, attachment = upload(client)
    other = client.post("/api/conversations", json={}).json()
    state = client.app.state.claimpilot
    with state.session() as session:
        session.add(
            Attachment(
                conversation_id=uuid.UUID(other["id"]),
                filename="bad.pdf",
                content_type="application/pdf",
                media_type="pdf",
                size_bytes=1,
                path="unused",
                replaces_attachment_id=uuid.UUID(attachment["id"]),
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    assert replace_file(client, conv, attachment).status_code == 200
    with state.session() as session:
        session.execute(delete(Conversation).where(Conversation.id == uuid.UUID(conv["id"])))
        session.commit()
    assert client.get(f"/api/conversations/{other['id']}").status_code == 200


def test_lost_commit_acknowledgement_does_not_delete_the_saved_replacement(client, monkeypatch):
    import uuid

    conv, attachment = upload(client)
    state = client.app.state.claimpilot
    original = Session.commit
    failed = False

    def commit(session):
        nonlocal failed
        replacement = any(
            isinstance(row, Attachment) and row.replaces_attachment_id
            for row in session.identity_map.values()
        )
        result = original(session)
        if replacement and not failed:
            failed = True
            raise RuntimeError("lost commit acknowledgement")
        return result

    monkeypatch.setattr(Session, "commit", commit)
    with pytest.raises(RuntimeError, match="commit acknowledgement"):
        replace_file(client, conv, attachment)
    saved = client.get(f"/api/conversations/{conv['id']}").json()
    replacement = saved["attachments"][-1]
    assert replacement["is_current"] and replacement["revision"] == 2
    with state.session() as session:
        row = session.get(Attachment, uuid.UUID(replacement["id"]))
        assert Path(row.path).is_file()
    assert replace_file(client, conv, attachment).json()["id"] == replacement["id"]
    assert len(client.get(f"/api/conversations/{conv['id']}").json()["attachments"]) == 2
