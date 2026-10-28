from __future__ import annotations

from pathlib import Path

import pytest
from langgraph.checkpoint.memory import MemorySaver

from api.agent.graph import (
    AgentDeps,
    _enforce_citations,
    build_graph,
    pending_interrupt,
    resume_review,
    run_turn,
    thread_config,
)
from api.agent.language import detect_language
from api.agent.required_facts import describe, missing_facts
from api.agent.schemas import ChatMessage, ClaimFacts, PolicyContext, ReviewDecision
from api.llm.provider import ProviderError, RecordedProvider

FIXTURE = Path(__file__).parent / "fixtures" / "agent" / "hit_and_run.json"

from tests.agent_corpus import FakeScorer, make_retriever  # noqa: E402


@pytest.fixture
def graph_and_provider():
    provider = RecordedProvider(FIXTURE)
    deps = AgentDeps(
        provider=provider,
        retriever=make_retriever(),
        risk_scorer=FakeScorer(),
        today=lambda: "2026-10-26",
    )
    return build_graph(deps, checkpointer=MemorySaver()), provider


def test_scripted_hit_and_run_conversation(graph_and_provider):
    graph, provider = graph_and_provider
    thread = "t1"
    policy = PolicyContext(product="vollkasko", deductible_eur=300)

    first = run_turn(
        graph,
        thread,
        "Gestern Abend hat jemand mein geparktes Auto auf dem Supermarktparkplatz in Köln angefahren und ist einfach weggefahren. Die hintere Stoßstange ist eingedrückt.",
        policy,
    )
    assert first["language"] == "de"
    assert first["facts"].event_type == "hit_and_run" and first["facts"].incident_date is None
    assert first["missing"] == ["incident_date"]
    assert first["followups_asked"] == 1 and first["status"] == "collecting"
    assert "Wann" in first["messages"][-1].content
    assert pending_interrupt(first) is None

    second = graph.invoke(
        {
            "messages": [
                ChatMessage(
                    role="user",
                    content="Das war am 25.10.2026 gegen 19 Uhr. Die Polizei habe ich nicht gerufen, Zeugen gab es keine.",
                )
            ],
            "attachments": 1,
        },
        thread_config(thread),
    )
    facts = second["facts"]
    assert (
        facts.incident_date == "2026-10-25" and facts.event_type == "hit_and_run"
    )  # merge kept the type
    assert (
        facts.police_report_filed is False
        and facts.damage_description == "Hintere Stoßstange eingedrückt"
    )
    assert second["followups_asked"] == 1  # follow-up asked exactly once
    assert facts.photos_attached is True  # one attachment came with this turn
    assert second["status"] == "awaiting_review"

    card = second["card"]
    cited = {c.clause_id for c in card.citations}
    assert {"A.2.2.2.2", "A.2.5.8", "E.1.1.1", "E.1.1.3"} <= cited
    assert card.risk is not None and card.risk.band == "medium" and len(card.risk.reasons) == 3
    assert card.coverage_status == "likely_covered"
    assert "[Z.9.9]" not in card.coverage_summary and "[A.2.2.2.2]" in card.coverage_summary
    assert "nicht belegte Klauselangabe" in card.coverage_summary
    assert card.missing_documents and card.next_steps

    interrupt = pending_interrupt(second)
    assert interrupt is not None and interrupt["card"]["status"] == "awaiting_review"
    assert graph.get_state(thread_config(thread)).next == ("human_review",)

    final = resume_review(
        graph,
        thread,
        ReviewDecision(
            decision="edit", facts_patch={"witnesses": True}, note="caller mentioned a witness"
        ),
    )
    assert final["status"] == "reviewed" and final["card"].status == "reviewed"
    assert (
        final["facts"].witnesses is True
        and final["card"].review.note == "caller mentioned a witness"
    )
    assert graph.get_state(thread_config(thread)).next == ()
    assert [c["tag"] for c in provider.calls] == ["extract", "followup", "extract", "compose"]


def test_compose_without_evidence_cites_nothing_and_skips_llm():
    provider = RecordedProvider(FIXTURE)
    deps = AgentDeps(
        provider=provider, retriever=None, risk_scorer=None, today=lambda: "2026-10-26"
    )
    graph = build_graph(deps, checkpointer=MemorySaver())
    run_turn(
        graph,
        "t2",
        "Someone hit my parked car and drove away yesterday evening in Cologne. Rear bumper dented.",
    )
    result = run_turn(graph, "t2", "It was on 2026-10-25, I did not call the police.")
    card = result["card"]
    assert card.coverage_status == "no_evidence" and card.citations == [] and card.risk is None
    assert "[" not in card.coverage_summary
    assert "claims handler" in card.coverage_summary  # detected English
    assert "compose" not in [c["tag"] for c in provider.calls]


def test_extract_failure_degrades_to_rephrase_request(tmp_path: Path):
    fixture = tmp_path / "bad.json"
    fixture.write_text('{"extract": [{"event_type": "spaceship"}, {"event_type": "spaceship"}]}')
    graph = build_graph(AgentDeps(provider=RecordedProvider(fixture)), checkpointer=MemorySaver())
    result = run_turn(graph, "t3", "asdf qwer")
    assert result["extract_failed"] is True
    assert "nicht verstanden" in result["messages"][-1].content
    assert result.get("followups_asked", 0) == 0


def test_followup_budget_moves_on_after_three_rounds(tmp_path: Path):
    fixture = tmp_path / "loop.json"
    empty = ClaimFacts().model_dump()
    fixture.write_text(
        __import__("json").dumps(
            {
                "extract": [empty] * 4,
                "followup": [
                    {"question": f"Frage {i}?", "asked_for": ["incident_date"]} for i in range(3)
                ],
            }
        )
    )
    graph = build_graph(
        AgentDeps(provider=RecordedProvider(fixture), retriever=None), checkpointer=MemorySaver()
    )
    for i in range(3):
        result = run_turn(graph, "t4", f"keine Ahnung {i}")
        assert result["status"] == "collecting" and result["followups_asked"] == i + 1
    result = run_turn(graph, "t4", "immer noch keine Ahnung")
    assert result["status"] == "awaiting_review" and result["card"].coverage_status == "no_evidence"


def test_enforce_citations_strips_unknown_ids():
    text, dropped = _enforce_citations("Covered [A.2.2.2.2] and [Q.1.1] here.", {"A.2.2.2.2"})
    assert text == "Covered [A.2.2.2.2] and here." and dropped == ["Q.1.1"]


def test_missing_facts_and_labels():
    assert missing_facts(ClaimFacts()) == [
        "incident_date",
        "event_type",
        "third_party_involved",
        "damage_description",
    ]
    facts = ClaimFacts(
        incident_date="2026-01-01",
        event_type="theft",
        third_party_involved=False,
        damage_description="x",
    )
    assert missing_facts(facts) == []
    assert (
        describe(["incident_date", "event_type", "location"], "en")
        == "date of the incident; what kind of incident it was"
    )


def test_facts_merge_rules():
    base = ClaimFacts(event_type="theft", location="Köln", photos_attached=True)
    merged = base.merge(ClaimFacts(event_type="unknown", location=None, incident_date="2026-01-02"))
    assert (
        merged.event_type == "theft"
        and merged.location == "Köln"
        and merged.incident_date == "2026-01-02"
    )
    assert merged.photos_attached is True


def test_detect_language():
    assert detect_language("Gestern hat jemand mein Auto angefahren und ist weggefahren.") == "de"
    assert detect_language("Someone hit my parked car and drove away.") == "en"
    assert detect_language("12345") == "de"


def test_recorded_provider_exhaustion(tmp_path: Path):
    fixture = tmp_path / "f.json"
    fixture.write_text('{"followup": [{"question": "Q?", "asked_for": []}]}')
    provider = RecordedProvider(fixture)
    from api.agent.schemas import ChatMessage, FollowupOutput

    first = provider.complete(
        [ChatMessage(role="user", content="hi")], response_schema=FollowupOutput, tag="followup"
    )
    assert first.parsed.question == "Q?"
    with pytest.raises(ProviderError, match="no recorded response #2"):
        provider.complete(
            [ChatMessage(role="user", content="hi")], response_schema=FollowupOutput, tag="followup"
        )
