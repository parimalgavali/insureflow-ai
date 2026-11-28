"""Recorded workflow contracts for five claim types; no live AI or risk-model evaluation."""

import json
import os
from pathlib import Path

import pytest

from api.agent.schemas import ClaimFacts, RiskSignal
from api.llm.provider import AnthropicProvider, OllamaProvider, RecordedProvider
from api.policy_text import prepare_pdf
from tests.test_api import ADJUSTER, parse_sse
from tests.test_api import client as client

ROOT = Path(__file__).parent / "fixtures/claim_scenarios"
POLICY = ROOT.parent / "claim_types_policy.pdf"
SCENARIOS = json.loads((ROOT / "scenarios.json").read_text())
MATRIX = [
    pytest.param(
        ROOT / f"{case['id']}{'_liability' if liability else ''}.json",
        case,
        "haftpflicht" if liability else case["product"],
        "likely_not_covered" if liability else "likely_covered",
        id=f"{case['id']}-{'haftpflicht' if liability else case['product']}",
    )
    for case in SCENARIOS
    for liability in (False, True)
]


def test_scenario_matrix_covers_required_types_and_policy_pages():
    assert {case["id"] for case in SCENARIOS} == {
        "collision",
        "theft",
        "glass",
        "vandalism",
        "storm_hail",
    }
    assert {case["id"]: case["product"] for case in SCENARIOS} == {
        "collision": "vollkasko",
        "theft": "teilkasko",
        "glass": "teilkasko",
        "vandalism": "vollkasko",
        "storm_hail": "teilkasko",
    }
    assert len(MATRIX) == 10
    pages, passages = prepare_pdf(POLICY)
    assert pages == len(passages) == 6
    for case in SCENARIOS:
        passage = passages[case["policy_page"] - 1]
        assert case["id"].split("_")[0] in passage.text.casefold()
        assert "haftpflicht" in passage.text and "excludes" in passage.text
        assert "fictional test wording" in passage.section_heading


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs Postgres")
@pytest.mark.parametrize("client,case,product,coverage_status", MATRIX, indirect=["client"])
def test_claim_type_intake_selected_policy_documents_and_human_handoff(
    client, case, product, coverage_status, monkeypatch
):
    state = client.app.state.claimpilot
    assert isinstance(state.provider, RecordedProvider)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def no_live_model(*args, **kwargs):
        pytest.fail("Scenario tests must not make paid/live model calls")

    monkeypatch.setattr(AnthropicProvider, "complete", no_live_model)
    monkeypatch.setattr(OllamaProvider, "complete", no_live_model)
    monkeypatch.setattr(
        state.retriever,
        "retrieve_many",
        lambda *a, **kw: pytest.fail("Selected policy must not fall through to demo wording"),
    )
    scored = []

    def score(facts, policy):
        scored.append((facts.model_copy(deep=True), policy.model_copy(deep=True)))
        return RiskSignal(
            score=0.25,
            band="low",
            reasons=["Synthetic scorer: complete test inputs."],
            model_version="scenario-stub",
        )

    monkeypatch.setattr(state.risk_scorer, "score", score)
    deductible = 0 if product == "haftpflicht" else 300
    response = client.post(
        "/api/conversations",
        json={"language": "en", "policy": {"product": product, "deductible_eur": deductible}},
    )
    assert response.status_code == 201
    conv = response.json()
    cid, claim_id = conv["id"], conv["claim_id"]
    messages = f"/api/conversations/{cid}/messages"
    claim_url = f"/api/claims/{claim_id}"
    uploaded = client.post(
        f"/api/conversations/{cid}/policy",
        files={"file": (POLICY.name, POLICY.read_bytes(), "application/pdf")},
    )
    assert uploaded.status_code == 200
    document_id = uploaded.json()["document"]["id"]
    prepared = client.post(f"/api/conversations/{cid}/policy/prepare")
    assert prepared.status_code == 200
    assert prepared.json()["document"]["status"] == "ready"
    assert prepared.json()["document"]["passage_count"] == 6

    first = client.post(messages, data={"text": case["turns"][0], "language": "en"})
    assert first.status_code == 200
    first_events = dict(parse_sse(first.text))
    assert first_events["facts"]["facts"]["event_type"] == case["id"]
    assert first_events["facts"]["facts"]["incident_date"] is None
    assert first_events["missing"]["missing"] == ["incident_date"]
    assert first_events["done"]["status"] == "collecting"
    assert "card" not in first_events and scored == []
    assert "date" in first_events["question"]["text"].casefold()
    assert client.post(claim_url + "/submit").status_code == 409
    assert (
        client.post(
            claim_url + "/review", json={"decision": "accept"}, headers=ADJUSTER
        ).status_code
        == 409
    )

    second = client.post(messages, data={"text": case["turns"][1], "language": "en"})
    assert second.status_code == 200
    events = dict(parse_sse(second.text))
    assert events["missing"]["missing"] == []
    assert events["done"]["status"] == "assessed" and not events["done"]["awaiting_review"]
    card = events["card"]["card"]
    expected_facts = ClaimFacts.model_validate(case["expected_facts"]).model_dump(mode="json")
    assert card["facts"] == expected_facts
    assert card["policy"]["product"] == product and card["policy"]["deductible_eur"] == deductible
    assert card["coverage_status"] == coverage_status
    assert (
        card["coverage_source"] == "uploaded_policy" and card["coverage_policy_id"] == document_id
    )
    assert card["coverage_policy_ready"] and not card["assessment_stale"]
    citations = {citation["clause_id"]: citation for citation in card["citations"]}
    assert {case["policy_clause"], "P.6"} <= citations.keys()
    event_citation = citations[case["policy_clause"]]
    assert event_citation["page"] == case["policy_page"]
    assert case["id"].split("_")[0] in event_citation["excerpt"].casefold()
    assert all(
        c["document_id"] == document_id
        and c["source_name"] == POLICY.name
        and c["source"] == "uploaded_policy"
        for c in citations.values()
    )
    assert card["missing_documents"] == case["expected_documents"]
    assert card["review"] is None
    assert len(scored) == 1 and scored[0][0].model_dump(mode="json") == expected_facts
    assert scored[0][1].product == product and scored[0][1].deductible_eur == deductible
    assert card["risk_status"] == "available" and card["risk"]["model_version"] == "scenario-stub"

    compose = next(call for call in state.provider.calls if call["tag"] == "compose")
    assert f"product {product} and deductible {deductible} EUR" in compose["system"]
    compose_facts = (
        compose["messages"][-1]["content"]
        .split("\n\nRetrieved source passages", 1)[0]
        .removeprefix("Claim facts (JSON):\n")
    )
    assert json.loads(compose_facts) == expected_facts
    assert event_citation["excerpt"] in compose["messages"][-1]["content"]
    assert f"[{case['policy_clause']}]" in compose["messages"][-1]["content"]
    restored = client.get(f"/api/conversations/{cid}").json()
    assert restored["status"] == "assessed" and restored["card"] == card
    assert restored["attachments"] == []  # Selected policy is not claim evidence.
    assert len(restored["messages"]) == 5
    checklist = restored["document_checklist"]
    assert {item["label"] for item in checklist} == set(case["expected_documents"])
    assert len(checklist) == len(case["expected_documents"])
    assert all(item["status"] == "missing" and item["attachment_ids"] == [] for item in checklist)
    assert client.get(f"/api/conversations/{cid}").json()["document_checklist"] == checklist

    handoff = client.post(claim_url + "/submit")
    assert handoff.status_code == 200
    submitted = handoff.json()
    assert submitted["status"] == submitted["card"]["status"] == "awaiting_review"
    assert submitted["submitted_at"] and submitted["card"]["review"] is None
    assert submitted["card"]["facts"] == expected_facts
    assert submitted["document_checklist"] == checklist
    assert client.post(claim_url + "/submit").json() == submitted
    assert [entry["kind"] for entry in submitted["history"]] == ["submitted"]
    assert client.get(f"/api/claims/review-queue/{claim_id}").status_code == 401
    reviewer_copy = client.get(f"/api/claims/review-queue/{claim_id}", headers=ADJUSTER).json()
    assert reviewer_copy == submitted
    assert client.post(claim_url + "/review", json={"decision": "accept"}).status_code == 401
    completed = client.post(
        claim_url + "/review",
        json={"decision": "accept", "note": f"Checked synthetic {case['id']} scenario."},
        headers=ADJUSTER,
    )
    assert completed.status_code == 200
    final = completed.json()
    assert final["status"] == "reviewed" and final["card"]["facts"] == expected_facts
    assert final["card"]["review"]["reviewer"] == "adjuster"
    assert [entry["kind"] for entry in final["history"]] == ["submitted", "review_completed"]
    assert [call["tag"] for call in state.provider.calls] == [
        "extract",
        "followup",
        "extract",
        "compose",
    ]
    assert len(scored) == 1
