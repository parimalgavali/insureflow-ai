"""Typed state shared by the agent, the API and the frontend."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Language = Literal["de", "en"]
EventType = Literal[
    "collision",
    "hit_and_run",
    "theft",
    "vandalism",
    "glass",
    "wild_animal",
    "storm_hail",
    "fire",
    "other",
    "unknown",
]
CoverageStatus = Literal["likely_covered", "likely_not_covered", "unclear", "no_evidence"]
ClaimStatus = Literal["collecting", "assessed", "awaiting_review", "reviewed"]
RiskBand = Literal["low", "medium", "high"]


class ClaimFacts(BaseModel):
    """What the policyholder has told us so far. Every field is optional; None = not yet known."""

    incident_date: str | None = Field(None, description="ISO date YYYY-MM-DD; null if unknown")
    incident_time: str | None = Field(None, description="HH:MM if mentioned")
    location: str | None = Field(None, description="Where it happened (city, street, car park …)")
    event_type: EventType = "unknown"
    description: str | None = Field(None, description="One-sentence summary of what happened")
    third_party_involved: bool | None = Field(None, description="Another vehicle/person involved?")
    third_party_known: bool | None = Field(None, description="Is the other party identified?")
    injuries: bool | None = None
    police_report_filed: bool | None = None
    witnesses: bool | None = None
    damage_description: str | None = None
    estimated_amount_eur: float | None = None
    vehicle_drivable: bool | None = None
    photos_attached: bool = False

    def merge(self, update: ClaimFacts) -> ClaimFacts:
        """Newer non-null values win; ``event_type`` 'unknown' never overwrites a known type."""
        data = self.model_dump()
        for key, value in update.model_dump().items():
            if value is None:
                continue
            if key == "event_type" and value == "unknown":
                continue
            if key == "photos_attached" and value is False:
                continue
            data[key] = value
        return ClaimFacts(**data)


class PolicyContext(BaseModel):
    """Seed-policy facts (from freMTPL2 sample + product choice) the agent may rely on."""

    product: Literal["haftpflicht", "teilkasko", "vollkasko"] = "vollkasko"
    deductible_eur: float = 300.0
    vehicle_age_years: int | None = None
    vehicle_power: int | None = None
    driver_age: int | None = None
    bonus_malus: int | None = None
    region: str | None = None


class Citation(BaseModel):
    clause_id: str
    title: str = ""
    excerpt: str
    page: int | None = None
    score: float | None = None

    @property
    def label(self) -> str:
        return f"AKB 2015 {self.clause_id}"


class RiskSignal(BaseModel):
    score: float = Field(ge=0.0, le=1.0, description="Model probability of the fraud label")
    band: RiskBand
    reasons: list[str] = Field(default_factory=list, max_length=3)
    model_version: str = "unknown"


class ReviewDecision(BaseModel):
    decision: Literal["accept", "edit", "request_info"]
    facts_patch: dict = Field(default_factory=dict)
    note: str | None = None
    reviewer: str = "adjuster"


class CostContext(BaseModel):
    """Expected claim cost for the policy profile (freMTPL2) — context only."""

    claims_per_year: float = Field(ge=0)
    claim_eur: float = Field(ge=0, description="expected amount per claim")
    annual_cost_eur: float = Field(ge=0, description="claims_per_year × claim_eur")
    portfolio_claim_eur: float = Field(ge=0, description="portfolio mean per claim, for scale")
    basis: str = "freMTPL2 (French motor TPL, 2004–2005)"


class ClaimCard(BaseModel):
    facts: ClaimFacts
    policy: PolicyContext
    coverage_status: CoverageStatus = "no_evidence"
    coverage_summary: str = ""
    citations: list[Citation] = Field(default_factory=list)
    risk: RiskSignal | None = None
    cost: CostContext | None = None
    missing_documents: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    status: ClaimStatus = "collecting"
    review: ReviewDecision | None = None


class ComposeOutput(BaseModel):
    """Structured output of the compose step; validated against retrieved clauses before use."""

    answer: str = Field(
        description="Reply to the policyholder in their language, with [A.2.2.1.4]-style citations"
    )
    coverage_status: CoverageStatus
    cited_clause_ids: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class FollowupOutput(BaseModel):
    question: str = Field(description="One friendly message asking for at most two missing facts")
    asked_for: list[str] = Field(default_factory=list, description="Field names being asked for")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
