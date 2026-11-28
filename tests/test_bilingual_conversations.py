"""Controlled bilingual difficult-conversation contracts, not live-model language evaluation."""

import json
import os
from pathlib import Path

import pytest

from api.agent.graph import thread_config
from api.agent.schemas import RiskSignal
from tests.test_api import client as client
from tests.test_api import parse_sse

ROOT = Path(__file__).parent / "fixtures/bilingual_scenarios"
MATRIX = [
    pytest.param(ROOT / f"{source}_to_{target}.json", source, target, id=f"{source}-to-{target}")
    for source, target in [("en", "en"), ("de", "de"), ("en", "de"), ("de", "en")]
]
pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs Postgres")


@pytest.mark.parametrize("client,source,target", MATRIX, indirect=["client"])
def test_unknown_answers_contradictions_corrections_and_language_switch(
    client, source, target, monkeypatch
):
    expected = json.loads((ROOT / f"{source}_to_{target}_expected.json").read_text())
    state = client.app.state.claimpilot
    scored = []

    def score(facts, policy):
        scored.append(facts.model_copy(deep=True))
        return RiskSignal(
            score=0.2,
            band="low",
            reasons=["Synthetic complete-input probe"],
            model_version="bilingual-stub",
        )

    monkeypatch.setattr(state.risk_scorer, "score", score)
    conv = client.post("/api/conversations", json={"language": source}).json()
    cid, claim_id = conv["id"], conv["claim_id"]
    get_url, messages_url, facts_url = (
        f"/api/conversations/{cid}",
        f"/api/conversations/{cid}/messages",
        f"/api/claims/{claim_id}/facts",
    )
    pdf = ROOT.parent / "claim_types_policy.pdf"
    client.post(
        get_url + "/policy", files={"file": (pdf.name, pdf.read_bytes(), "application/pdf")}
    )
    assert client.post(get_url + "/policy/prepare").json()["document"]["status"] == "ready"

    for turn in range(2):
        result = client.post(
            messages_url,
            data={"text": expected["turns"][turn], "language": expected["languages"][turn]},
        )
        assert result.status_code == 200
        events = dict(parse_sse(result.text))
        facts = events["facts"]["facts"]
        assert events["done"]["status"] == "collecting"
        assert set(events["missing"]["missing"]) == {"incident_date", "third_party_involved"}
        assert events["question"]["text"] == expected["questions"][turn]
        assert "card" not in events
        for field in ["incident_date", "third_party_involved", "estimated_amount_eur", "witnesses"]:
            assert facts[field] is None
        assert facts["photos_attached"] is False
        assert all(facts[key] == value for key, value in expected["stable_facts"].items())
        saved = client.get(get_url).json()
        assert saved["id"] == cid and saved["language"] == expected["languages"][turn]
        assert (
            saved["card"]["risk"] is None
            and saved["card"]["risk_status"] == "insufficient_information"
        )
        assert not scored
        assert client.post(f"/api/claims/{claim_id}/submit").status_code == 409

    ready = client.post(messages_url, data={"text": expected["turns"][2], "language": target})
    events = dict(parse_sse(ready.text))
    card = events["card"]["card"]
    assert events["done"]["status"] == "assessed"
    assert card["facts"]["incident_date"] == "2026-10-24"
    assert card["facts"]["estimated_amount_eur"] == 1800
    assert card["facts"]["third_party_involved"] is False
    assert card["facts"]["witnesses"] is None
    assert (
        card["coverage_status"] == "unclear"
        and card["coverage_uncertainty"] == "conflicting_evidence"
    )
    assert card["coverage_summary"] == expected["answers"][0]
    assert card["risk"] is None and card["risk_status"] == "insufficient_information" and not scored
    assert card["risk_missing"] == ["witnesses"]
    assert {c["clause_id"] for c in card["citations"]} == {"P.1", "P.6"}
    assert all(c["source_name"] == pdf.name for c in card["citations"])
    calls_before = len(state.provider.calls)
    bad = client.patch(
        facts_url, json={"facts_patch": {"incident_date": "2026-02-30", "estimated_amount_eur": -1}}
    )
    assert bad.status_code == 422 and len(state.provider.calls) == calls_before
    assert client.get(get_url).json()["card"]["facts"] == card["facts"]

    corrected = client.patch(
        facts_url,
        json={
            "facts_patch": {
                "incident_date": "2026-10-25",
                "estimated_amount_eur": 900,
                "witnesses": False,
            }
        },
    )
    assert corrected.status_code == 200
    data = corrected.json()
    assert (
        data["card"]["facts"]["incident_date"] == "2026-10-25"
        and data["card"]["facts"]["estimated_amount_eur"] == 900
    )
    assert (
        data["card"]["coverage_summary"] == expected["answers"][1]
        and not data["card"]["assessment_stale"]
    )
    assert (
        data["card"]["coverage_status"] == "likely_covered"
        and data["card"]["coverage_uncertainty"] is None
    )
    assert (
        len(scored) == 1
        and scored[0].incident_date == "2026-10-25"
        and scored[0].estimated_amount_eur == 900
    )
    assert scored[0].witnesses is False
    changes = next(entry["changes"] for entry in data["history"] if entry["kind"] == "corrected")
    assert {change["field"]: (change["before"], change["after"]) for change in changes} == {
        "incident_date": ("2026-10-24", "2026-10-25"),
        "estimated_amount_eur": (1800, 900),
        "witnesses": (None, False),
    }
    # An explicit "not known" selection must clear a previously confirmed risk answer.
    unknown = client.patch(facts_url, json={"facts_patch": {"witnesses": None}}).json()
    assert unknown["card"]["facts"]["witnesses"] is None and unknown["card"]["risk"] is None
    assert unknown["card"]["risk_status"] == "insufficient_information" and len(scored) == 1
    assert unknown["card"]["coverage_summary"] == expected["answers"][2]
    saved = client.get(get_url).json()
    assert saved["language"] == target and saved["card"] == unknown["card"]
    assert saved["messages"][1]["content"] == expected["turns"][0]
    assert all(
        saved["card"]["facts"][key] == value for key, value in expected["stable_facts"].items()
    )
    assert len(saved["history"]) == 4
    assert state.graph.get_state(thread_config(cid)).values["language"] == target
    composition_calls = [call for call in state.provider.calls if call["tag"] == "compose"]
    assert len(composition_calls) == 3
    for call in composition_calls:
        assert ("Answer in German" if target == "de" else "Answer in English") in call["system"]
    compose_facts = (
        composition_calls[-1]["messages"][-1]["content"]
        .split("\n\nRetrieved source passages", 1)[0]
        .removeprefix("Claim facts (JSON):\n")
    )
    assert json.loads(compose_facts)["witnesses"] is None
