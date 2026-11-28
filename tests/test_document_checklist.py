import os
from pathlib import Path

import pytest

from tests.test_api import ADJUSTER, MSG1, MSG2
from tests.test_evidence_api import client as client
from tests.test_evidence_replacement import pdf_bytes

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs Postgres")
FOLLOWUP = Path(__file__).parent / "fixtures/agent/hit_and_run_followup.json"


def assessed(client, document_type="repair_estimate"):
    conv = client.post("/api/conversations", json={"language": "en"}).json()
    client.post(f"/api/conversations/{conv['id']}/messages", data={"text": MSG1})
    client.post(
        f"/api/conversations/{conv['id']}/messages",
        data={"text": MSG2, "document_type": document_type},
        files={
            "file": (
                "estimate.pdf",
                (Path(__file__).parent / "fixtures/claim_evidence.pdf").read_bytes(),
                "application/pdf",
            )
        },
    )
    saved = client.get(f"/api/conversations/{conv['id']}").json()
    return conv, saved


def kind_item(saved, kind):
    return next(
        item
        for item in saved["document_checklist"]
        if item["document_type"] == kind and item["origin"] == "assessment"
    )


def confirm_url(conv, item):
    return f"/api/claims/{conv['claim_id']}/documents/{item['id']}/confirmation"


def test_saved_files_are_uploaded_not_confirmed(client):
    conv, saved = assessed(client)
    estimate = kind_item(saved, "repair_estimate")
    assert estimate["status"] == "uploaded" and estimate["attachment_ids"] == [
        saved["attachments"][0]["id"]
    ]
    assert kind_item(saved, "damage_photo")["status"] == "missing"
    assert kind_item(saved, "police_report")["status"] == "missing"
    assert (
        client.get(f"/api/conversations/{conv['id']}").json()["document_checklist"]
        == saved["document_checklist"]
    )
    assert (
        client.get(f"/api/claims/{conv['claim_id']}").json()["document_checklist"]
        == saved["document_checklist"]
    )
    assert (
        client.post(
            confirm_url(conv, estimate), json={"attachment_ids": estimate["attachment_ids"]}
        ).status_code
        == 401
    )
    client.post(f"/api/claims/{conv['claim_id']}/submit")
    confirmed = client.post(
        confirm_url(conv, estimate),
        json={"attachment_ids": estimate["attachment_ids"]},
        headers=ADJUSTER,
    )
    assert confirmed.status_code == 200
    data = confirmed.json()
    assert kind_item(data, "repair_estimate")["status"] == "confirmed"
    assert (
        client.post(
            confirm_url(conv, estimate),
            json={"attachment_ids": estimate["attachment_ids"]},
            headers=ADJUSTER,
        ).json()
        == data
    )
    assert sum(e["kind"] == "documents_confirmed" for e in data["history"]) == 1
    photos = kind_item(data, "damage_photo")
    assert (
        client.post(
            confirm_url(conv, photos), json={"attachment_ids": []}, headers=ADJUSTER
        ).status_code
        == 422
    )


@pytest.mark.parametrize("client", [FOLLOWUP], indirect=True)
def test_new_reviewer_request_needs_fresh_link_and_replacement_needs_confirmation_again(client):
    conv, saved = assessed(client)
    estimate = kind_item(saved, "repair_estimate")
    client.post(f"/api/claims/{conv['claim_id']}/submit")
    client.post(
        confirm_url(conv, estimate),
        json={"attachment_ids": estimate["attachment_ids"]},
        headers=ADJUSTER,
    )
    requested = client.post(
        f"/api/claims/{conv['claim_id']}/review",
        json={
            "decision": "request_info",
            "note": "Please send a clearer estimate.",
            "requested_documents": [
                {"label": "Clear repair estimate", "document_type": "repair_estimate"}
            ],
        },
        headers=ADJUSTER,
    ).json()
    new = next(item for item in requested["document_checklist"] if item["origin"] == "reviewer")
    assert new["status"] == "missing" and new["attachment_ids"] == []
    assert kind_item(requested, "repair_estimate")["status"] == "confirmed"
    old = saved["attachments"][0]
    replacement = client.put(
        f"/api/conversations/{conv['id']}/attachments/{old['id']}",
        files={"file": ("clear.pdf", pdf_bytes("readable"), "application/pdf")},
    ).json()
    current = client.get(f"/api/conversations/{conv['id']}").json()
    assert kind_item(current, "repair_estimate")["status"] == "uploaded"
    assert kind_item(current, "repair_estimate")["attachment_ids"] == [replacement["id"]]
    assert (
        next(item for item in current["document_checklist"] if item["id"] == new["id"])["status"]
        == "uploaded"
    )
    client.post(
        f"/api/conversations/{conv['id']}/messages",
        data={"text": "The repair estimate is clearer now."},
    )
    client.post(f"/api/claims/{conv['claim_id']}/submit")
    assert (
        client.post(
            confirm_url(conv, estimate),
            json={"attachment_ids": [old["id"]]},
            headers=ADJUSTER,
        ).status_code
        == 409
    )
    verified = client.post(
        confirm_url(conv, estimate), json={"attachment_ids": [replacement["id"]]}, headers=ADJUSTER
    ).json()
    assert kind_item(verified, "repair_estimate")["status"] == "confirmed"


def test_manual_links_and_exclusions_survive_reload_and_replacement(client):
    conv, saved = assessed(client)
    item = kind_item(saved, "repair_estimate")
    old = saved["attachments"][0]
    link = f"/api/claims/{conv['claim_id']}/documents/{item['id']}/attachments/{old['id']}"
    removed = client.delete(link).json()
    assert kind_item(removed, "repair_estimate")["status"] == "missing"
    assert (
        client.get(f"/api/conversations/{conv['id']}").json()["document_checklist"]
        == removed["document_checklist"]
    )
    assert client.delete(link).json() == removed
    replacement = client.put(
        f"/api/conversations/{conv['id']}/attachments/{old['id']}",
        files={"file": ("clear.pdf", pdf_bytes("readable"), "application/pdf")},
    ).json()
    current = client.get(f"/api/conversations/{conv['id']}").json()
    assert kind_item(current, "repair_estimate")["status"] == "missing"
    new_link = (
        f"/api/claims/{conv['claim_id']}/documents/{item['id']}/attachments/{replacement['id']}"
    )
    linked = client.put(new_link).json()
    assert kind_item(linked, "repair_estimate")["status"] == "uploaded"
    assert client.put(new_link).json() == linked
    police = kind_item(linked, "police_report")
    assert (
        client.put(
            f"/api/claims/{conv['claim_id']}/documents/{police['id']}/attachments/{replacement['id']}"
        ).status_code
        == 422
    )
    other = client.post("/api/conversations", json={}).json()
    assert (
        client.put(
            f"/api/claims/{other['claim_id']}/documents/{item['id']}/attachments/{replacement['id']}"
        ).status_code
        == 404
    )


@pytest.mark.parametrize("client", [FOLLOWUP], indirect=True)
def test_policy_file_and_a_photo_fact_do_not_complete_document_requests(client):
    conv, saved = assessed(client)
    result = client.patch(
        f"/api/claims/{conv['claim_id']}/facts", json={"facts_patch": {"photos_attached": True}}
    ).json()
    assert result["card"]["facts"]["photos_attached"]
    assert kind_item(result, "damage_photo")["status"] == "missing"
    policy = (Path(__file__).parent / "fixtures/sample_policy.pdf").read_bytes()
    assert (
        client.post(
            f"/api/conversations/{conv['id']}/policy",
            files={"file": ("policy.pdf", policy, "application/pdf")},
        ).status_code
        == 200
    )
    restored = client.get(f"/api/conversations/{conv['id']}").json()
    assert kind_item(restored, "police_report")["status"] == "missing"
    assert kind_item(restored, "damage_photo")["status"] == "missing"
    assert len(restored["attachments"]) == 1


def test_generic_verified_document_can_be_linked_explicitly_but_is_not_auto_confirmed(client):
    conv, saved = assessed(client, document_type="other_document")
    item = kind_item(saved, "repair_estimate")
    assert item["status"] == "missing"
    file_id = saved["attachments"][0]["id"]
    linked = client.put(
        f"/api/claims/{conv['claim_id']}/documents/{item['id']}/attachments/{file_id}"
    ).json()
    assert kind_item(linked, "repair_estimate")["status"] == "uploaded"
    assert kind_item(linked, "damage_photo")["status"] == "missing"
