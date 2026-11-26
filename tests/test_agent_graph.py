from __future__ import annotations

import json
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
    submit_for_review,
    thread_config,
)
from api.agent.language import detect_language
from api.agent.required_facts import describe, missing_facts
from api.agent.schemas import ChatMessage, ClaimFacts, PolicyContext, ReviewDecision, RiskSignal
from api.llm.provider import ProviderError, RecordedProvider

FIXTURE = Path(__file__).parent / "fixtures" / "agent" / "hit_and_run.json"

from tests.agent_corpus import FakeScorer, make_retriever  # noqa: E402


@pytest.fixture
def graph_and_provider():
    provider = RecordedProvider(FIXTURE.with_name("hit_and_run_followup.json"))
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
    assert second["status"] == "assessed"

    card = second["card"]
    cited = {c.clause_id for c in card.citations}
    assert {"A.2.2.2.2", "A.2.5.8", "E.1.1.1", "E.1.1.3"} <= cited
    assert card.risk is not None and card.risk.band == "medium" and len(card.risk.reasons) == 3
    assert card.coverage_status == "likely_covered"
    assert "[Z.9.9]" not in card.coverage_summary and "[A.2.2.2.2]" in card.coverage_summary
    assert "nicht belegte Klauselangabe" in card.coverage_summary
    assert card.missing_documents and card.next_steps

    interrupt = pending_interrupt(second)
    assert interrupt is not None and interrupt["card"]["status"] == "assessed"
    assert graph.get_state(thread_config(thread)).next == ("submit",)
    with pytest.raises(ValueError, match="submitted"):
        resume_review(graph, thread, ReviewDecision(decision="accept"))
    submitted = submit_for_review(graph, thread)
    assert submitted["status"] == "awaiting_review"
    assert submitted["card"].review is None
    checkpoint = graph.get_state(thread_config(thread)).config
    assert submit_for_review(graph, thread)["status"] == "awaiting_review"
    assert graph.get_state(thread_config(thread)).config == checkpoint
    assert graph.get_state(thread_config(thread)).next == ("human_review",)

    final = resume_review(
        graph,
        thread,
        ReviewDecision(
            decision="edit",
            facts_patch={"witnesses": True, "photos_attached": False},
            note="caller mentioned a witness",
        ),
    )
    assert final["status"] == "awaiting_review" and final["card"].review is None
    assert final["card"].assessment_stale is False
    assert final["facts"].photos_attached is False
    assert final["card"].corrections[0].field == "witnesses"
    final = resume_review(
        graph, thread, ReviewDecision(decision="accept", note="caller mentioned a witness")
    )
    assert final["status"] == "reviewed" and final["card"].status == "reviewed"
    assert (
        final["facts"].witnesses is True
        and final["card"].review.note == "caller mentioned a witness"
    )
    assert graph.get_state(thread_config(thread)).next == ()
    assert [c["tag"] for c in provider.calls] == [
        "extract",
        "followup",
        "extract",
        "compose",
        "compose",
    ]


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


def test_information_request_reopens_the_claim_and_requires_resubmission():
    provider = RecordedProvider(FIXTURE.with_name("hit_and_run_followup.json"))
    graph = build_graph(
        AgentDeps(provider=provider, retriever=make_retriever(), risk_scorer=FakeScorer()),
        checkpointer=MemorySaver(),
    )
    thread = "request-info"
    run_turn(graph, thread, "Mein geparktes Auto wurde angefahren.")
    run_turn(graph, thread, "Am 25.10.2026, keine Polizei.")
    submit_for_review(graph, thread)
    requested = resume_review(
        graph,
        thread,
        ReviewDecision(
            decision="request_info", note="Please provide the police report and repair estimate."
        ),
    )
    assert requested["status"] == requested["card"].status == "information_needed"
    assert "Please provide" in requested["messages"][-1].content
    assert graph.get_state(thread_config(thread)).next == ()
    with pytest.raises(ValueError, match="not ready"):
        submit_for_review(graph, thread)
    updated = run_turn(
        graph,
        thread,
        "Die Polizei wurde inzwischen informiert. Der Kostenvoranschlag beträgt 1200 Euro.",
    )
    assert updated["status"] == "assessed"
    assert updated["facts"].police_report_filed is True
    assert updated["facts"].estimated_amount_eur == 1200
    assert updated["card"].review is None
    assert any("Please provide" in m["content"] for m in provider.calls[-2]["messages"])
    assert submit_for_review(graph, thread)["status"] == "awaiting_review"
    assert resume_review(graph, thread, ReviewDecision(decision="accept"))["status"] == "reviewed"


def test_information_request_needs_a_clear_note_and_cannot_change_facts():
    from pydantic import ValidationError

    from api.agent.schemas import ReviewRequest

    for body in (
        {"decision": "request_info"},
        {"decision": "request_info", "note": "   "},
        {"decision": "request_info", "note": "x" * 2001},
        {"decision": "request_info", "note": "Details please", "facts_patch": {"witnesses": True}},
    ):
        with pytest.raises(ValidationError):
            ReviewRequest(**body)
    assert (
        ReviewRequest(decision="request_info", note="  Police report please  ").note
        == "Police report please"
    )


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
    assert result["status"] == "assessed" and result["card"].coverage_status == "no_evidence"


@pytest.fixture
def correction_context():
    provider = RecordedProvider(FIXTURE.with_name("hit_and_run_followup.json"))
    deps = AgentDeps(provider=provider, retriever=make_retriever(), risk_scorer=FakeScorer())
    graph = build_graph(deps, checkpointer=MemorySaver())
    run_turn(graph, "corrections", "Mein geparktes Auto wurde angefahren.")
    run_turn(graph, "corrections", "Am 25.10.2026, keine Polizei.")
    submit_for_review(graph, "corrections")
    return graph, deps, provider


def test_corrections_refresh_coverage_and_risk_using_the_corrected_facts(tmp_path):
    fixture = json.loads(FIXTURE.with_name("hit_and_run_followup.json").read_text())
    fixture["compose"][1].update(
        {
            "answer": "Wild animal cover [A.2.2.1.4].",
            "cited_clause_ids": ["A.2.2.1.4"],
        }
    )
    path = tmp_path / "corrected.json"
    path.write_text(json.dumps(fixture))
    provider = RecordedProvider(path)

    class Scorer:
        def __init__(self):
            self.inputs = []

        def score(self, facts, policy):
            self.inputs.append(facts.model_copy())
            return RiskSignal(
                score=0.1 if facts.police_report_filed else 0.8,
                band="low" if facts.police_report_filed else "high",
                reasons=[
                    "police report present" if facts.police_report_filed else "no police report"
                ],
            )

    scorer = Scorer()
    graph = build_graph(
        AgentDeps(provider=provider, retriever=make_retriever(), risk_scorer=scorer),
        checkpointer=MemorySaver(),
    )
    run_turn(graph, "fresh", "Mein geparktes Auto wurde angefahren.")
    run_turn(graph, "fresh", "Am 25.10.2026, keine Polizei.")
    initial = submit_for_review(graph, "fresh")
    assert initial["card"].risk.band == "high"
    corrected = resume_review(
        graph,
        "fresh",
        ReviewDecision(
            decision="edit",
            facts_patch={
                "event_type": "wild_animal",
                "police_report_filed": True,
                "photos_attached": False,
            },
        ),
    )
    assert corrected["status"] == "awaiting_review" and corrected["card"].review is None
    assert corrected["card"].assessment_stale is False
    assert corrected["card"].risk.band == "low"
    assert corrected["card"].citations[0].clause_id == "A.2.2.1.4"
    assert scorer.inputs[-1].event_type == "wild_animal"
    assert scorer.inputs[-1].police_report_filed is True
    assert {c.field for c in corrected["card"].corrections} == {"event_type", "police_report_filed"}
    assert [c["tag"] for c in provider.calls].count("extract") == 2
    assert graph.get_state(thread_config("fresh")).next == ("human_review",)
    assert resume_review(graph, "fresh", ReviewDecision(decision="accept"))["status"] == "reviewed"


@pytest.mark.parametrize("failure", ["retrieval", "risk", "composition"])
def test_failed_reassessment_saves_facts_and_blocks_completion_until_retry(
    correction_context, monkeypatch, failure
):
    graph, deps, provider = correction_context
    original = graph.get_state(thread_config("corrections")).values["card"]
    if failure == "retrieval":
        monkeypatch.setattr(deps, "retriever", None)
    elif failure == "risk":
        monkeypatch.setattr(deps, "risk_scorer", None)
    else:
        complete = provider.complete

        def fail_compose(*args, **kwargs):
            if kwargs.get("tag") == "compose":
                raise ProviderError("simulated answer failure")
            return complete(*args, **kwargs)

        monkeypatch.setattr(provider, "complete", fail_compose)
    failed = resume_review(
        graph, "corrections", ReviewDecision(decision="edit", facts_patch={"witnesses": True})
    )
    assert failed["facts"].witnesses is True
    assert failed["card"].assessment_stale is True
    assert failed["card"].assessment_error
    assert failed["card"].coverage_summary == original.coverage_summary
    assert failed["card"].review is None
    with pytest.raises(ValueError, match="out-of-date"):
        resume_review(graph, "corrections", ReviewDecision(decision="accept"))
    monkeypatch.undo()
    refreshed = resume_review(graph, "corrections", ReviewDecision(decision="reassess"))
    assert refreshed["card"].assessment_stale is False
    assert refreshed["card"].assessment_error is None
    assert refreshed["facts"].witnesses is True
    assert refreshed["card"].corrections[0].field == "witnesses"
    assert (
        resume_review(graph, "corrections", ReviewDecision(decision="accept"))["status"]
        == "reviewed"
    )


def test_clearing_a_required_fact_keeps_the_correction_and_allows_an_information_request(
    correction_context,
):
    graph, _, _ = correction_context
    corrected = resume_review(
        graph, "corrections", ReviewDecision(decision="edit", facts_patch={"incident_date": None})
    )
    assert corrected["facts"].incident_date is None
    assert corrected["card"].assessment_stale is True
    assert corrected["card"].corrections[0].after is None
    requested = resume_review(
        graph,
        "corrections",
        ReviewDecision(decision="request_info", note="Please confirm the incident date."),
    )
    assert requested["status"] == "information_needed"
    assert requested["card"].review.decision == "request_info"


def test_invalid_corrections_and_combined_completion_are_rejected():
    from pydantic import ValidationError

    from api.agent.schemas import ReviewRequest

    for patch in (
        {"incident_date": "2026-02-30"},
        {"incident_date": "yesterday"},
        {"incident_time": "25:00"},
        {"estimated_amount_eur": -1},
        {"estimated_amount_eur": float("inf")},
        {"witnesses": "maybe"},
    ):
        with pytest.raises(ValidationError):
            ReviewRequest(decision="edit", facts_patch=patch)
    for body in (
        {"decision": "edit"},
        {"decision": "accept", "facts_patch": {"witnesses": True}},
        {"decision": "reassess", "facts_patch": {"witnesses": True}},
    ):
        with pytest.raises(ValidationError):
            ReviewRequest(**body)


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


def test_review_facts_patch_only_accepts_known_typed_fields():
    # stored reviews stay readable whatever they contain; only new requests are checked
    assert ReviewDecision(decision="edit", facts_patch={"old": 1}, note="x" * 5000).note
    import pydantic

    from api.agent.schemas import ReviewRequest

    ok = ReviewRequest(decision="edit", facts_patch={"estimated_amount_eur": "1200"})
    assert ok.facts_patch == {"estimated_amount_eur": 1200.0}
    for bad in ({"fraud_score": 0}, {"event_type": "act_of_god"}, {"injuries": "maybe"}):
        with pytest.raises(pydantic.ValidationError):
            ReviewRequest(decision="edit", facts_patch=bad)
