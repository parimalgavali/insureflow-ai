"""The ClaimPilot agent as a LangGraph state graph.

    extract → check_missing ─┬─ ask_followup → END (wait for the user)
                             └─ retrieve → score_risk → compose → human_review (interrupt) → END

Every LLM call goes through ``Provider.complete`` so tests replay recorded responses; retrieval and
risk scoring are injected (``AgentDeps``) so the graph can run with an in-memory corpus.
"""

from __future__ import annotations

import json
import operator
import re
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
    FollowupOutput,
    Language,
    PolicyContext,
    ReviewDecision,
    RiskSignal,
)
from api.llm.provider import Provider, ProviderError

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
    cost: CostContext | None
    card: ClaimCard | None
    status: ClaimStatus
    review: ReviewDecision | None


def _conversation(state: AgentState) -> list[ChatMessage]:
    return [m for m in state.get("messages", []) if m.role in ("user", "assistant")]


def _last_user_text(state: AgentState) -> str:
    for message in reversed(state.get("messages", [])):
        if message.role == "user":
            return message.content
    return ""


def build_graph(deps: AgentDeps, checkpointer=None):
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
        return {
            "language": language,
            "facts": facts,
            "policy": state.get("policy") or PolicyContext(),
            "extract_failed": failed,
            "status": state.get("status") or "collecting",
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
        cost = deps.cost_estimator.estimate(state["policy"]) if deps.cost_estimator else None
        if deps.risk_scorer is None:
            return {"risk": None, "cost": cost}
        return {"risk": deps.risk_scorer.score(state["facts"], state["policy"]), "cost": cost}

    def compose(state: AgentState) -> dict:
        facts, policy, language = state["facts"], state["policy"], state["language"]
        retrieved = state.get("retrieved") or []
        if not retrieved:
            output = _no_evidence_output(language)
        else:
            output = _compose_with_llm(deps, state, retrieved)
        allowed = {c.clause_id for c in retrieved}
        answer, dropped = _enforce_citations(output.answer, allowed)
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
        card = ClaimCard(
            facts=facts,
            policy=policy,
            coverage_status=output.coverage_status if retrieved else "no_evidence",
            coverage_summary=answer,
            citations=[c for c in retrieved if c.clause_id in cited] or retrieved[:3],
            risk=state.get("risk"),
            cost=state.get("cost"),
            missing_documents=output.missing_documents,
            next_steps=output.next_steps,
            status="awaiting_review",
        )
        return {
            "messages": [ChatMessage(role="assistant", content=answer)],
            "card": card,
            "status": "awaiting_review",
        }

    def human_review(state: AgentState) -> dict:
        card: ClaimCard = state["card"]
        decision_raw = interrupt({"card": card.model_dump(), "language": state["language"]})
        decision = ReviewDecision.model_validate(decision_raw)
        facts = state["facts"]
        if decision.facts_patch:
            facts = facts.merge(ClaimFacts(**{**facts.model_dump(), **decision.facts_patch}))
        reviewed = card.model_copy(
            update={"facts": facts, "status": "reviewed", "review": decision}
        )
        return {"facts": facts, "card": reviewed, "review": decision, "status": "reviewed"}

    graph = StateGraph(AgentState)
    graph.add_node("extract", extract)
    graph.add_node("check_missing", check_missing)
    graph.add_node("ask_followup", ask_followup)
    graph.add_node("retrieve", retrieve)
    graph.add_node("score_risk", score_risk)
    graph.add_node("compose", compose)
    graph.add_node("human_review", human_review)
    graph.add_edge(START, "extract")
    graph.add_edge("extract", "check_missing")
    graph.add_conditional_edges("check_missing", route_after_missing)
    graph.add_edge("ask_followup", END)
    graph.add_edge("retrieve", "score_risk")
    graph.add_edge("score_risk", "compose")
    graph.add_edge("compose", "human_review")
    graph.add_edge("human_review", END)
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
    return graph.invoke(Command(resume=decision.model_dump()), thread_config(thread_id))


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
