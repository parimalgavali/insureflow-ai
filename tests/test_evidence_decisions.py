import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from api.agent.graph import thread_config
from db.models import EvidenceSuggestion
from tests.test_evidence_api import client as client
from tests.test_evidence_api import endpoint, provider, upload

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs Postgres")


def prepared(client, monkeypatch):
    conv, attachment = upload(client)
    calls = provider(monkeypatch, client.app.state.claimpilot)
    read = client.post(endpoint(conv, attachment)).json()
    return conv, read["suggestions"], calls


def decision_url(conv, suggestion):
    return f"/api/claims/{conv['claim_id']}/evidence-suggestions/{suggestion['id']}/decision"


def test_accept_and_reject_are_individual_saved_and_safe_to_retry(client, monkeypatch):
    conv, suggestions, calls = prepared(client, monkeypatch)
    url = decision_url(conv, suggestions[0])
    accepted = client.post(url, json={"decision": "accept", "expected_current": None})
    assert accepted.status_code == 200
    data = accepted.json()
    assert data["card"]["facts"]["estimated_amount_eur"] == 1200
    assert [s["status"] for s in data["attachments"][0]["suggestions"]] == ["accepted", "pending"]
    history = data["history"]
    assert sum(e["kind"] == "evidence_accepted" for e in history) == 1
    assert any(e["note"] == "estimate.pdf, page 1" for e in history)
    again = client.post(url, json={"decision": "accept", "expected_current": None}).json()
    assert again == data
    rejected = client.post(
        decision_url(conv, suggestions[1]), json={"decision": "reject", "expected_current": None}
    ).json()
    assert rejected["card"]["facts"]["incident_date"] is None
    assert rejected["attachments"][0]["suggestions"][1]["status"] == "rejected"
    assert (
        client.post(
            decision_url(conv, suggestions[1]),
            json={"decision": "reject", "expected_current": None},
        ).json()
        == rejected
    )
    assert (
        client.post(url, json={"decision": "reject", "expected_current": None}).status_code == 409
    )
    assert len(calls) == 1  # Decisions never rerun document extraction.


def test_conflicts_require_current_value_and_explicit_replacement(client, monkeypatch):
    conv, suggestions, _ = prepared(client, monkeypatch)
    facts_url = f"/api/claims/{conv['claim_id']}/facts"
    assert (
        client.patch(facts_url, json={"facts_patch": {"estimated_amount_eur": 900}}).status_code
        == 200
    )
    url = decision_url(conv, suggestions[0])
    assert (
        client.post(
            url, json={"decision": "accept", "expected_current": None, "replace_existing": True}
        ).status_code
        == 409
    )
    assert client.post(url, json={"decision": "accept", "expected_current": 900}).status_code == 409
    accepted = client.post(
        url, json={"decision": "accept", "expected_current": 900, "replace_existing": True}
    ).json()
    assert accepted["card"]["facts"]["estimated_amount_eur"] == 1200
    # A replay cannot overwrite a correction made after this suggestion was accepted.
    assert (
        client.patch(facts_url, json={"facts_patch": {"estimated_amount_eur": 800}}).status_code
        == 200
    )
    replay = client.post(
        url, json={"decision": "accept", "expected_current": 900, "replace_existing": True}
    ).json()
    assert replay["card"]["facts"]["estimated_amount_eur"] == 800


def test_suggestion_cannot_be_decided_through_another_claim_or_without_baseline(
    client, monkeypatch
):
    conv, suggestions, _ = prepared(client, monkeypatch)
    other = client.post("/api/conversations", json={}).json()
    assert (
        client.post(
            decision_url(other, suggestions[0]),
            json={"decision": "accept", "expected_current": None},
        ).status_code
        == 404
    )
    assert (
        client.post(decision_url(conv, suggestions[0]), json={"decision": "accept"}).status_code
        == 422
    )
    assert (
        client.post(
            decision_url(conv, {"id": str(uuid.uuid4())}),
            json={"decision": "reject", "expected_current": None},
        ).status_code
        == 404
    )


def test_failed_accept_commit_can_resume_and_blocks_intervening_changes(client, monkeypatch):
    conv, suggestions, _ = prepared(client, monkeypatch)
    original = Session.commit
    failed = False

    def commit(session):
        nonlocal failed
        if not failed and any(
            isinstance(row, EvidenceSuggestion) and row.status == "accepted"
            for row in session.identity_map.values()
        ):
            failed = True
            raise RuntimeError("simulated decision write failure")
        return original(session)

    monkeypatch.setattr(Session, "commit", commit)
    url = decision_url(conv, suggestions[0])
    with pytest.raises(RuntimeError, match="decision write"):
        client.post(url, json={"decision": "accept", "expected_current": None})
    restored = client.get(f"/api/conversations/{conv['id']}").json()
    assert restored["card"]["facts"]["estimated_amount_eur"] is None
    assert restored["attachments"][0]["suggestions"][0]["status"] == "applying"
    assert (
        client.patch(
            f"/api/claims/{conv['claim_id']}/facts", json={"facts_patch": {"location": "Berlin"}}
        ).status_code
        == 409
    )
    assert client.post(f"/api/claims/{conv['claim_id']}/submit").status_code == 409
    assert (
        client.post(
            f"/api/conversations/{conv['id']}/messages", data={"text": "Another message"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            decision_url(conv, suggestions[1]),
            json={"decision": "reject", "expected_current": None},
        ).status_code
        == 409
    )
    pdf = (Path(__file__).parent / "fixtures/sample_policy.pdf").read_bytes()
    assert (
        client.post(
            f"/api/conversations/{conv['id']}/policy",
            files={"file": ("policy.pdf", pdf, "application/pdf")},
        ).status_code
        == 409
    )
    result = client.post(url, json={"decision": "accept", "expected_current": None}).json()
    assert result["card"]["facts"]["estimated_amount_eur"] == 1200
    assert result["attachments"][0]["suggestions"][0]["status"] == "accepted"
    assert sum(e["kind"] == "evidence_accepted" for e in result["history"]) == 1
    assert sum(e["kind"] == "corrected" for e in result["history"]) == 1


def test_graph_confirmation_resumes_interrupted_node_with_same_action_id(client, monkeypatch):
    from api.agent.graph import correct_customer_facts

    conv, suggestions, _ = prepared(client, monkeypatch)
    graph = client.app.state.claimpilot.graph
    # Pause with the confirmation input checkpointed before the correction node runs.
    snapshot = graph.get_state(thread_config(conv["id"]))
    action_id = "evidence-" + uuid.UUID(suggestions[0]["id"]).hex
    result = graph.invoke(
        {"customer_patch": {"estimated_amount_eur": 1200}, "customer_action_id": action_id},
        thread_config(conv["id"]),
        interrupt_before=["customer_correct"],
    )
    assert result["facts"].estimated_amount_eur is None
    assert graph.get_state(thread_config(conv["id"])).next
    resumed = correct_customer_facts(
        graph, conv["id"], {"estimated_amount_eur": 1200}, action_id=action_id
    )
    assert resumed["customer_action_id"] == action_id
    assert not graph.get_state(thread_config(conv["id"])).next
    assert len(resumed["messages"]) == len(snapshot.values["messages"]) + 1


@pytest.mark.parametrize(
    "client", [Path(__file__).parent / "fixtures/agent/hit_and_run_followup.json"], indirect=True
)
def test_accepting_changed_facts_refreshes_the_assessment(client, monkeypatch):
    from tests.test_api import MSG2

    conv, suggestions, _ = prepared(client, monkeypatch)
    client.post(f"/api/conversations/{conv['id']}/messages", data={"text": MSG2})
    state = client.app.state.claimpilot
    before = sum(call["tag"] == "compose" for call in state.provider.calls)
    result = client.post(
        decision_url(conv, suggestions[0]), json={"decision": "accept", "expected_current": None}
    ).json()
    assert result["status"] == "assessed"
    assert result["card"]["facts"]["estimated_amount_eur"] == 1200
    assert result["card"]["assessment_stale"] is False
    assert sum(call["tag"] == "compose" for call in state.provider.calls) == before + 1
    assert any(e["kind"] == "assessment_refreshed" for e in result["history"])


@pytest.mark.parametrize(
    "client", [Path(__file__).parent / "fixtures/agent/hit_and_run_followup.json"], indirect=True
)
def test_failed_reassessment_keeps_accepted_fact_and_blocks_submission(client, monkeypatch):
    from api.llm.provider import ProviderError
    from tests.test_api import MSG2

    conv, suggestions, _ = prepared(client, monkeypatch)
    client.post(f"/api/conversations/{conv['id']}/messages", data={"text": MSG2})
    state = client.app.state.claimpilot
    original = state.provider.complete

    def fail_assessment(*args, **kwargs):
        if kwargs.get("tag") == "compose":
            raise ProviderError("temporary assessment failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(state.provider, "complete", fail_assessment)
    result = client.post(
        decision_url(conv, suggestions[0]), json={"decision": "accept", "expected_current": None}
    ).json()
    assert result["card"]["facts"]["estimated_amount_eur"] == 1200
    assert result["card"]["assessment_stale"]
    assert result["attachments"][0]["suggestions"][0]["status"] == "accepted"
    assert any(e["kind"] == "assessment_refresh_failed" for e in result["history"])
    assert client.post(f"/api/claims/{conv['claim_id']}/submit").status_code == 409


def test_competing_retries_confirm_only_once(client, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor

    conv, suggestions, _ = prepared(client, monkeypatch)
    url = decision_url(conv, suggestions[0])
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda _: client.post(url, json={"decision": "accept", "expected_current": None}),
                range(2),
            )
        )
    assert all(r.status_code == 200 for r in results)
    assert results[0].json() == results[1].json()
    assert sum(e["kind"] == "evidence_accepted" for e in results[0].json()["history"]) == 1
