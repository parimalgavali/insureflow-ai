"""The ClaimPilot agent as a LangGraph state graph.

    extract → check_missing ─┬─ ask_followup → END (wait for the user)
                             └─ retrieve → score_risk → compose → submit → human_review → END

Every LLM call goes through ``Provider.complete`` so tests replay recorded responses; retrieval and
risk scoring are injected (``AgentDeps``) so the graph can run with an in-memory corpus.
"""

from __future__ import annotations

import json
import logging
import operator
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Annotated, Any, Literal, Protocol, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from api.agent.language import detect_language
from api.agent.required_facts import describe, missing_facts
from api.agent.schemas import (
    ChatMessage,
    Citation,
    ClaimCard,
    ClaimFacts,
    ClaimStatus,
    ComposeOutput,
    CostContext,
    FactChange,
    FactsPatch,
    FollowupOutput,
    Language,
    PolicyContext,
    ReviewDecision,
    ReviewRequest,
    RiskSignal,
    RiskStatus,
)
from api.llm.provider import Provider, ProviderError
from ml.risk_inputs import missing_risk_inputs

PROMPTS_DIR = Path(__file__).parent / "prompts"
MAX_FOLLOWUPS = 3
TOP_K = 5
MAX_CITATIONS = 8
CLAUSE_REF = re.compile(r"\[([A-Z]\.\d+(?:\.\d+)*)\]")
LANGUAGE_NAMES = {"de": "German", "en": "English"}

# German policy-language queries per event type; the corpus is German whatever the user speaks.
EVENT_QUERIES: dict[str, list[str]] = {
    "collision": [
        "Unfall Beschädigung des Fahrzeugs Vollkasko",
        "Pflichten im Schadenfall Anzeige",
    ],
    "hit_and_run": [
        "Unfall: Schäden am Fahrzeug durch ein unmittelbar von außen plötzlich mit mechanischer "
        "Gewalt einwirkendes Ereignis (Vollkasko)",
        "Aufklärungspflicht: Unfallstelle nicht verlassen, Polizei, wahrheitsgemäße Angaben",
    ],
    "theft": ["Entwendung des Fahrzeugs Teilkasko", "Anzeige bei der Polizei bei Entwendung"],
    "vandalism": [
        "mut- oder böswillige Handlungen betriebsfremder Personen",
        "Anzeige bei der Polizei",
    ],
    "glass": ["Bruchschäden an der Verglasung Glasbruch Teilkasko"],
    "wild_animal": ["Zusammenstoß mit Haarwild Teilkasko", "Wildschaden Anzeige bei der Polizei"],
    "storm_hail": ["Sturm Hagel Blitzschlag Überschwemmung Teilkasko"],
    "fire": ["Brand und Explosion Teilkasko", "Brandschaden Anzeige bei der Polizei"],
    "other": [
        "Welche Ereignisse sind in der Kaskoversicherung versichert",
        "Pflichten im Schadenfall",
    ],
    "unknown": ["Welche Ereignisse sind in der Kaskoversicherung versichert"],
}


# Asked for every claim: the reporting duty, and the deductible for Kasko products.
COMMON_QUERIES = ["Anzeigepflicht: Schadenereignis innerhalb einer Woche anzeigen"]
DEDUCTIBLE_QUERY = (
    "Selbstbeteiligung wird bei jedem Schadenereignis von der Entschädigung abgezogen"
)
PER_QUERY = 3


class RiskScorer(Protocol):
    def score(self, facts: ClaimFacts, policy: PolicyContext) -> RiskSignal | None: ...


class CostEstimator(Protocol):
    def estimate(self, policy: PolicyContext) -> CostContext | None: ...


class RetrieverLike(Protocol):
    def retrieve(self, query: str, k: int = 5, lang: Any = "de") -> list: ...

    def retrieve_many(self, queries, k: int = 5) -> list: ...


@dataclass
class AgentDeps:
    provider: Provider
    retriever: RetrieverLike | None = None
    risk_scorer: RiskScorer | None = None
    cost_estimator: CostEstimator | None = None
    today: Callable[[], str] = field(default=lambda: date.today().isoformat())
    prompts_dir: Path = PROMPTS_DIR

    def prompt(self, name: str, **values: Any) -> str:
        return (self.prompts_dir / f"{name}.md").read_text(encoding="utf-8").format(**values)


class AgentState(TypedDict, total=False):
    messages: Annotated[list[ChatMessage], operator.add]
    language: Language
    facts: ClaimFacts
    policy: PolicyContext
    missing: list[str]
    attachments: Annotated[int, operator.add]
    followups_asked: int
    extract_failed: bool
    retrieved: list[Citation]
    risk: RiskSignal | None
    risk_status: RiskStatus
    risk_missing: list[str]
    cost: CostContext | None
    card: ClaimCard | None
    status: ClaimStatus
    review: ReviewDecision | None
    reassessment_needed: bool
    submission_id: str
    review_action_id: str
    review_changes: list[FactChange]
    customer_patch: dict | None
    customer_action_id: str
    customer_changes: list[FactChange]
    assessment_target: Literal["assessed", "awaiting_review"]
    customer_correction_message: str | None
    customer_assessment_message: str | None


def _conversation(state: AgentState) -> list[ChatMessage]:
    return [m for m in state.get("messages", []) if m.role in ("user", "assistant")]


def _last_user_text(state: AgentState) -> str:
    for message in reversed(state.get("messages", [])):
        if message.role == "user":
            return message.content
    return ""


def build_graph(deps: AgentDeps, checkpointer=None):
    def route_entry(state: AgentState) -> Literal["customer_correct", "extract"]:
        return "customer_correct" if state.get("customer_patch") is not None else "extract"

    def customer_correct(state: AgentState) -> dict:
        facts = state["facts"]
        patch = FactsPatch.model_validate(state["customer_patch"]).model_dump(exclude_unset=True)
        updated = ClaimFacts(**{**facts.model_dump(), **patch})
        changes = [
            FactChange(field=k, before=getattr(facts, k), after=getattr(updated, k))
            for k in patch
            if getattr(facts, k) != getattr(updated, k)
        ]
        missing = missing_facts(updated)
        status = "collecting" if missing else "assessed"
        card = state.get("card") or ClaimCard(facts=facts, policy=state["policy"])
        message = None
        if missing:
            message = (
                "Ergänzen Sie die fehlenden Angaben vor der Bewertung."
                if state["language"] == "de"
                else "Fill in the missing claim details before the assessment can be refreshed."
            )
        card = card.model_copy(
            update={
                "facts": updated,
                "status": status,
                "assessment_stale": not missing or bool(card.coverage_summary or card.risk),
                "assessment_error": message,
                "review": None,
                "corrections": changes or card.corrections,
            }
        )
        card = ClaimCard.model_validate(card.model_dump())
        correction_message = None
        if changes:
            label = (
                "Bestätigte Korrekturen" if state["language"] == "de" else "Confirmed corrections"
            )
            correction_message = f"{label}: {json.dumps(patch, ensure_ascii=False)}"
        return {
            "facts": updated,
            "card": card,
            "status": status,
            "missing": missing,
            "customer_patch": None,
            "customer_changes": changes,
            "assessment_target": "assessed",
            "review": None,
            "followups_asked": 0,
            "customer_correction_message": correction_message,
            "customer_assessment_message": None,
            "messages": [ChatMessage(role="user", content=correction_message)]
            if correction_message
            else [],
        }

    def route_customer(state: AgentState) -> Literal["reassess", "__end__"]:
        return END if state.get("missing") else "reassess"

    def extract(state: AgentState) -> dict:
        language = state.get("language") or detect_language(_last_user_text(state))
        facts = state.get("facts") or ClaimFacts()
        system = deps.prompt("extract_v1", today=deps.today(), language=language)
        conversation = _conversation(state)
        update, failed = None, False
        for attempt in range(2):
            try:
                completion = deps.provider.complete(
                    conversation, system=system, response_schema=ClaimFacts, tag="extract"
                )
                update = completion.parsed
                break
            except ProviderError as exc:
                if attempt == 1:
                    failed = True
                else:
                    conversation = [
                        *conversation,
                        ChatMessage(
                            role="user",
                            content=f"Your previous answer was invalid ({exc}). "
                            "Return valid ClaimFacts.",
                        ),
                    ]
        if isinstance(update, ClaimFacts):
            facts = facts.merge(update)
        if state.get("attachments", 0) > 0 and not facts.photos_attached:
            facts = facts.model_copy(update={"photos_attached": True})
        policy = state.get("policy") or PolicyContext()
        risk_missing = missing_risk_inputs(facts, policy)
        return {
            "language": language,
            "facts": facts,
            "policy": policy,
            "risk": None,
            "risk_status": "insufficient_information" if risk_missing else "pending",
            "risk_missing": risk_missing,
            "extract_failed": failed,
            "status": "collecting",
            "card": None,
            "review": None,
            "followups_asked": (
                0
                if state.get("status") == "information_needed"
                else state.get("followups_asked", 0)
            ),
        }

    def check_missing(state: AgentState) -> dict:
        return {"missing": missing_facts(state["facts"])}

    def route_after_missing(state: AgentState) -> Literal["ask_followup", "retrieve"]:
        if state.get("extract_failed"):
            return "ask_followup"
        if state["missing"] and state.get("followups_asked", 0) < MAX_FOLLOWUPS:
            return "ask_followup"
        return "retrieve"

    def ask_followup(state: AgentState) -> dict:
        language = state["language"]
        if state.get("extract_failed"):
            text = (
                "Entschuldigung, das habe ich nicht verstanden. "
                "Können Sie kurz beschreiben, was passiert ist?"
                if language == "de"
                else "Sorry, I didn't catch that. Could you briefly describe what happened?"
            )
            return {
                "messages": [ChatMessage(role="assistant", content=text)],
                "status": "collecting",
            }
        system = deps.prompt(
            "followup_v1",
            language_name=LANGUAGE_NAMES[language],
            missing=describe(state["missing"], language),
        )
        completion = deps.provider.complete(
            _conversation(state), system=system, response_schema=FollowupOutput, tag="followup"
        )
        question = (
            completion.parsed.question if isinstance(completion.parsed, FollowupOutput) else ""
        )
        return {
            "messages": [ChatMessage(role="assistant", content=question)],
            "followups_asked": state.get("followups_asked", 0) + 1,
            "status": "collecting",
        }

    def retrieve(state: AgentState) -> dict:
        """Top hits per query, interleaved: scores are not comparable across queries, so a global
        sort would let one well-matched duty clause crowd out the coverage clause."""
        if deps.retriever is None:
            return {"retrieved": []}
        facts, policy, language = state["facts"], state["policy"], state["language"]
        queries = [*EVENT_QUERIES.get(facts.event_type, []), *COMMON_QUERIES]
        if policy.product != "haftpflicht":
            queries.append(DEDUCTIBLE_QUERY)
        per_query = [list(deps.retriever.retrieve_many([q], k=PER_QUERY)) for q in queries]
        if facts.description:
            per_query.append(
                list(deps.retriever.retrieve(facts.description, k=PER_QUERY, lang=language))
            )
        ordered: dict[str, Citation] = {}
        for rank in range(PER_QUERY):
            for hits in per_query:
                if rank < len(hits):
                    chunk, score = hits[rank].chunk, float(hits[rank].score)
                    if chunk.clause_id not in ordered:
                        ordered[chunk.clause_id] = Citation(
                            clause_id=chunk.clause_id,
                            title=chunk.title,
                            excerpt=chunk.text[:600],
                            page=chunk.page,
                            score=round(score, 4),
                        )
        return {"retrieved": list(ordered.values())[:MAX_CITATIONS]}

    def score_risk(state: AgentState) -> dict:
        cost = None
        if deps.cost_estimator:
            try:
                cost = deps.cost_estimator.estimate(state["policy"])
            except Exception:  # noqa: BLE001
                logging.getLogger("claimpilot.agent").warning("cost context unavailable")
        missing = missing_risk_inputs(state["facts"], state["policy"])
        if missing:
            return {
                "risk": None,
                "cost": cost,
                "risk_status": "insufficient_information",
                "risk_missing": missing,
            }
        if deps.risk_scorer is None:
            return {"risk": None, "cost": cost, "risk_status": "unavailable", "risk_missing": []}
        try:
            risk = deps.risk_scorer.score(state["facts"], state["policy"])
        except Exception:  # noqa: BLE001
            logging.getLogger("claimpilot.agent").warning("risk scoring unavailable")
            risk = None
        return {
            "risk": risk,
            "cost": cost,
            "risk_status": "available" if risk else "unavailable",
            "risk_missing": [],
        }

    def compose(state: AgentState) -> dict:
        facts, policy, language = state["facts"], state["policy"], state["language"]
        retrieved = state.get("retrieved") or []
        if not retrieved:
            output = _no_evidence_output(language)
        else:
            output = _compose_with_llm(deps, state, retrieved)
        allowed = {c.clause_id for c in retrieved}
        answer, dropped = _enforce_citations(output.answer, allowed)
        answer = answer.replace("**", "")  # chat bubbles render plain text
        cited = [cid for cid in output.cited_clause_ids if cid in allowed]
        for cid in CLAUSE_REF.findall(answer):
            if cid not in cited:
                cited.append(cid)
        if dropped:
            note = (
                " (Hinweis: eine nicht belegte Klauselangabe wurde entfernt.)"
                if language == "de"
                else " (Note: an unsupported clause reference was removed.)"
            )
            answer += note
        uncertainty = output.coverage_uncertainty
        coverage_status = output.coverage_status if retrieved else "no_evidence"
        if not retrieved or not cited:
            fallback = _no_evidence_output(language)
            answer = fallback.answer
            output = fallback
            coverage_status = "no_evidence"
            uncertainty = "missing_policy_wording"
        elif dropped:
            coverage_status = "unclear"
            uncertainty = "human_review"
        elif uncertainty:
            coverage_status = "unclear"
        elif coverage_status == "unclear":
            uncertainty = "human_review"
        card = ClaimCard(
            facts=facts,
            policy=policy,
            coverage_status=coverage_status,
            coverage_uncertainty=uncertainty,
            coverage_summary=answer,
            citations=[c for c in retrieved if c.clause_id in cited] or retrieved[:3],
            risk=state.get("risk"),
            risk_status=state.get("risk_status", "pending"),
            risk_missing=state.get("risk_missing", []),
            cost=state.get("cost"),
            missing_documents=output.missing_documents,
            next_steps=output.next_steps,
            status="assessed",
        )
        return {
            "messages": [ChatMessage(role="assistant", content=answer)],
            "card": card,
            "status": "assessed",
        }

    def submit(state: AgentState) -> dict:
        confirmed = interrupt({"action": "submit", "card": state["card"].model_dump()})
        if confirmed is not True:
            raise ValueError("submission requires customer confirmation")
        if state["card"].assessment_stale:
            raise ValueError("refresh the assessment before submitting")
        card = state["card"].model_copy(update={"status": "awaiting_review"})
        return {"card": card, "status": "awaiting_review", "submission_id": uuid.uuid4().hex}

    def human_review(state: AgentState) -> dict:
        card: ClaimCard = state["card"]
        decision_raw = interrupt({"card": card.model_dump(), "language": state["language"]})
        decision = ReviewDecision.model_validate(decision_raw)
        ReviewRequest(**decision.model_dump(exclude={"reviewer"}))
        facts = state["facts"]
        if decision.decision == "accept" and card.assessment_stale:
            raise ValueError("refresh the out-of-date assessment before completing the review")
        action_id = uuid.uuid4().hex
        if decision.decision in ("edit", "reassess"):
            updated = ClaimFacts(**{**facts.model_dump(), **decision.facts_patch})
            changes = [
                FactChange(field=key, before=getattr(facts, key), after=getattr(updated, key))
                for key in decision.facts_patch
                if getattr(facts, key) != getattr(updated, key)
            ]
            corrected = card.model_copy(
                update={
                    "facts": updated,
                    "assessment_stale": True,
                    "assessment_error": None,
                    "corrections": changes or card.corrections,
                    "review": None,
                }
            )
            corrected = ClaimCard.model_validate(corrected.model_dump())
            return {
                "facts": updated,
                "card": corrected,
                "status": "awaiting_review",
                "review": decision,
                "reassessment_needed": True,
                "review_action_id": action_id,
                "review_changes": changes,
                "assessment_target": "awaiting_review",
            }
        if decision.decision == "request_info":
            request = ReviewRequest(**decision.model_dump(exclude={"reviewer"}))
            label = (
                "Rückfrage des Sachbearbeiters" if state["language"] == "de" else "Reviewer request"
            )
            card = card.model_copy(update={"status": "information_needed", "review": decision})
            return {
                "card": card,
                "review": decision,
                "status": "information_needed",
                "messages": [ChatMessage(role="assistant", content=f"{label}: {request.note}")],
                "review_action_id": action_id,
                "reassessment_needed": False,
                "review_changes": [],
            }
        reviewed = card.model_copy(
            update={"facts": facts, "status": "reviewed", "review": decision}
        )
        return {
            "facts": facts,
            "card": reviewed,
            "review": decision,
            "status": "reviewed",
            "review_action_id": action_id,
            "reassessment_needed": False,
            "review_changes": [],
        }

    def reassess(state: AgentState) -> dict:
        """Refresh authoritative corrected facts without extracting them again from old chat."""
        card = state["card"]
        target = state.get("assessment_target", "awaiting_review")
        try:
            if missing_facts(state["facts"]):
                raise ValueError("missing claim facts")
            refreshed = {**state, **retrieve(state)}
            if not refreshed.get("retrieved"):
                raise ValueError("coverage evidence unavailable")
            refreshed.update(score_risk(refreshed))
            if (
                refreshed.get("risk") is None
                and refreshed.get("risk_status") != "insufficient_information"
            ):
                raise ValueError("risk assessment unavailable")
            composed = compose(refreshed)["card"]
            if composed.coverage_status == "no_evidence":
                raise ValueError("coverage assessment unavailable")
            fresh_card = composed.model_copy(
                update={
                    "status": target,
                    "corrections": card.corrections,
                }
            )
            return {
                "card": fresh_card,
                "retrieved": refreshed["retrieved"],
                "risk": refreshed["risk"],
                "risk_status": refreshed["risk_status"],
                "risk_missing": refreshed["risk_missing"],
                "cost": refreshed.get("cost"),
                "status": target,
                "reassessment_needed": False,
                **(
                    {
                        "customer_assessment_message": fresh_card.coverage_summary,
                        "messages": [
                            ChatMessage(role="assistant", content=fresh_card.coverage_summary)
                        ],
                    }
                    if target == "assessed"
                    else {}
                ),
            }
        except Exception as exc:  # noqa: BLE001
            logging.getLogger("claimpilot.agent").warning(
                "reassessment failed: %s", type(exc).__name__
            )
            message = (
                "Die Angaben wurden gespeichert, aber die Bewertung konnte nicht aktualisiert "
                "werden. Die bisherige Einschätzung ist veraltet. Erneut prüfen oder weitere "
                "Angaben anfordern."
                if state["language"] == "de"
                else "Corrections were saved, but the assessment could not be refreshed. Previous "
                "guidance is out of date. Retry the assessment or request more information."
            )
            if target == "assessed":
                message = (
                    "Ihre Änderungen wurden gespeichert. Die Bewertung konnte nicht aktualisiert "
                    "werden. Versuchen Sie es vor dem Einreichen erneut."
                    if state["language"] == "de"
                    else "Your changes were saved, but the assessment could not be refreshed. "
                    "Retry before submitting the claim."
                )
            return {
                "card": card.model_copy(
                    update={"assessment_stale": True, "assessment_error": message}
                ),
                "status": target,
                "reassessment_needed": False,
                **(
                    {
                        "customer_assessment_message": message,
                        "messages": [ChatMessage(role="assistant", content=message)],
                    }
                    if target == "assessed"
                    else {}
                ),
            }

    def route_after_review(state: AgentState) -> Literal["reassess", "__end__"]:
        return "reassess" if state.get("reassessment_needed") else END

    def route_after_reassessment(state: AgentState) -> Literal["submit", "human_review"]:
        return "submit" if state.get("assessment_target") == "assessed" else "human_review"

    graph = StateGraph(AgentState)
    graph.add_node("extract", extract)
    graph.add_node("check_missing", check_missing)
    graph.add_node("ask_followup", ask_followup)
    graph.add_node("retrieve", retrieve)
    graph.add_node("score_risk", score_risk)
    graph.add_node("compose", compose)
    graph.add_node("submit", submit)
    graph.add_node("human_review", human_review)
    graph.add_node("reassess", reassess)
    graph.add_node("customer_correct", customer_correct)
    graph.add_conditional_edges(START, route_entry)
    graph.add_conditional_edges("customer_correct", route_customer)
    graph.add_edge("extract", "check_missing")
    graph.add_conditional_edges("check_missing", route_after_missing)
    graph.add_edge("ask_followup", END)
    graph.add_edge("retrieve", "score_risk")
    graph.add_edge("score_risk", "compose")
    graph.add_edge("compose", "submit")
    graph.add_edge("submit", "human_review")
    graph.add_conditional_edges("human_review", route_after_review)
    graph.add_conditional_edges("reassess", route_after_reassessment)
    return graph.compile(checkpointer=checkpointer)


def _no_evidence_output(language: Language) -> ComposeOutput:
    if language == "de":
        answer = (
            "Ich habe in den Musterbedingungen (AKB 2015) keine passende Klausel zu Ihrem Fall "
            "gefunden und kann deshalb keine Aussage zur Deckung machen. Ein Sachbearbeiter prüft "
            "Ihren Fall. Hilfreich wären Fotos der Schäden und ein kurzer Ablauf des Geschehens."
        )
        docs, steps = ["Fotos der Schäden"], ["Fall wird an einen Sachbearbeiter übergeben"]
    else:
        answer = (
            "I could not find a clause in the model terms (AKB 2015) that covers your situation, "
            "so I cannot comment on coverage. A claims handler will review your case. Photos of "
            "the damage and a short account of what happened would help."
        )
        docs, steps = ["Photos of the damage"], ["Case handed to a claims handler for review"]
    return ComposeOutput(
        answer=answer,
        coverage_status="no_evidence",
        cited_clause_ids=[],
        missing_documents=docs,
        next_steps=steps,
    )


def _compose_with_llm(
    deps: AgentDeps, state: AgentState, retrieved: list[Citation]
) -> ComposeOutput:
    facts, policy, language = state["facts"], state["policy"], state["language"]
    system = deps.prompt(
        "compose_v1",
        language_name=LANGUAGE_NAMES[language],
        product=policy.product,
        deductible=f"{policy.deductible_eur:.0f}",
    )
    clauses = "\n\n".join(f"[{c.clause_id}] {c.title}\n{c.excerpt}" for c in retrieved)
    risk = state.get("risk")
    content = (
        f"Claim facts (JSON):\n{facts.model_dump_json(indent=2)}\n\n"
        f"Retrieved AKB 2015 clauses:\n{clauses}\n\n"
        f"Risk signal (for your awareness only; do not mention a score to the user): "
        f"{risk.band if risk else 'n/a'}"
    )
    messages = [*_conversation(state), ChatMessage(role="user", content=content)]
    try:
        completion = deps.provider.complete(
            messages, system=system, response_schema=ComposeOutput, tag="compose", max_tokens=1500
        )
    except ProviderError:
        return _no_evidence_output(language)
    assert isinstance(completion.parsed, ComposeOutput)
    return completion.parsed


def _enforce_citations(answer: str, allowed: set[str]) -> tuple[str, list[str]]:
    """Strip clause references the retriever did not return; the model may not invent citations."""
    dropped = [cid for cid in CLAUSE_REF.findall(answer) if cid not in allowed]
    for cid in dropped:
        answer = answer.replace(f"[{cid}]", "")
    return re.sub(r"\s{2,}", " ", answer).strip(), dropped


def thread_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def run_turn(graph, thread_id: str, user_text: str, policy: PolicyContext | None = None) -> dict:
    """Feed one user message into the conversation and run the graph until it waits again."""
    payload: dict[str, Any] = {"messages": [ChatMessage(role="user", content=user_text)]}
    if policy is not None:
        payload["policy"] = policy
    return graph.invoke(payload, thread_config(thread_id))


def resume_review(graph, thread_id: str, decision: ReviewDecision) -> dict:
    snapshot = graph.get_state(thread_config(thread_id))
    if snapshot.next != ("human_review",):
        raise ValueError("claim must be submitted before review")
    ReviewRequest(**decision.model_dump(exclude={"reviewer"}))
    if decision.decision == "accept" and snapshot.values["card"].assessment_stale:
        raise ValueError("refresh the out-of-date assessment before completing the review")
    return graph.invoke(Command(resume=decision.model_dump()), thread_config(thread_id))


def submit_for_review(graph, thread_id: str) -> dict:
    snapshot = graph.get_state(thread_config(thread_id))
    if snapshot.values.get("status") in ("awaiting_review", "reviewed"):
        return snapshot.values
    if snapshot.next != ("submit",):
        raise ValueError("claim is not ready to submit")
    if snapshot.values["card"].assessment_stale:
        raise ValueError("refresh the assessment before submitting")
    return graph.invoke(Command(resume=True), thread_config(thread_id))


def correct_customer_facts(graph, thread_id: str, patch: dict, *, refresh: bool = False) -> dict:
    config = thread_config(thread_id)
    snapshot = graph.get_state(config)
    if snapshot.values.get("status") not in ("collecting", "assessed", "information_needed"):
        raise ValueError("customer corrections are only available before submission")
    if not snapshot.values.get("facts"):
        raise ValueError("describe the incident before editing collected facts")
    patch = FactsPatch.model_validate(patch).model_dump(exclude_unset=True)
    if snapshot.next == ("reassess",) and snapshot.values.get("assessment_target") == "assessed":
        if refresh or all(getattr(snapshot.values["facts"], k) == v for k, v in patch.items()):
            return graph.invoke(None, config)
        raise ValueError("retry the pending assessment before making more corrections")
    if not refresh and all(getattr(snapshot.values["facts"], k) == v for k, v in patch.items()):
        return snapshot.values
    return graph.invoke({"customer_patch": patch, "customer_action_id": uuid.uuid4().hex}, config)


def pending_interrupt(result: dict) -> dict | None:
    interrupts = result.get("__interrupt__") or []
    return interrupts[0].value if interrupts else None


def to_json(state: dict) -> str:
    def default(obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return str(obj)

    return json.dumps(
        {k: v for k, v in state.items() if k != "__interrupt__"},
        default=default,
        ensure_ascii=False,
    )
