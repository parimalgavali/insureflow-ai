"""Typed state shared by the agent, the API and the frontend."""

from __future__ import annotations

import re
from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ml.risk_inputs import missing_risk_inputs

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
ClaimStatus = Literal["collecting", "assessed", "awaiting_review", "information_needed", "reviewed"]
CoverageUncertainty = Literal[
    "missing_facts", "missing_policy_wording", "conflicting_evidence", "human_review"
]
RiskBand = Literal["low", "medium", "high"]
RiskStatus = Literal["pending", "available", "insufficient_information", "unavailable"]


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


class FactsPatch(ClaimFacts):
    """Adjuster corrections: only known ClaimFacts fields, with their types."""

    model_config = ConfigDict(extra="forbid")
    estimated_amount_eur: float | None = Field(None, ge=0, allow_inf_nan=False)

    @field_validator("incident_date")
    @classmethod
    def _valid_date(cls, value: str | None) -> str | None:
        if value is not None:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValueError("use YYYY-MM-DD for the incident date")
            date.fromisoformat(value)
        return value

    @field_validator("incident_time")
    @classmethod
    def _valid_time(cls, value: str | None) -> str | None:
        if value is not None:
            if not re.fullmatch(r"\d{2}:\d{2}", value):
                raise ValueError("use HH:MM for the incident time")
            time.fromisoformat(value)
        return value


class CustomerCorrection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    facts_patch: dict

    @field_validator("facts_patch")
    @classmethod
    def _valid_patch(cls, value: dict) -> dict:
        if not value:
            raise ValueError("provide the facts to correct")
        return FactsPatch.model_validate(value).model_dump(exclude_unset=True)


class ReviewRequest(BaseModel):
    """Body of POST /api/claims/{id}/review; the reviewer comes from the credential."""

    model_config = ConfigDict(extra="forbid")

    decision: Literal["accept", "edit", "request_info", "reassess"]
    facts_patch: dict = Field(default_factory=dict)
    note: str | None = Field(None, max_length=2000)

    @field_validator("facts_patch")
    @classmethod
    def _known_facts_only(cls, value: dict) -> dict:
        return FactsPatch.model_validate(value).model_dump(exclude_unset=True)

    @model_validator(mode="after")
    def _information_request(self):
        if self.decision == "edit" and not self.facts_patch:
            raise ValueError("provide the facts to correct")
        if self.decision in ("accept", "reassess") and self.facts_patch:
            raise ValueError("save corrections separately before completing the review")
        if self.decision == "request_info":
            if not self.note or not self.note.strip():
                raise ValueError("explain what information is needed")
            if self.facts_patch:
                raise ValueError("request information separately from correcting facts")
            self.note = self.note.strip()
        return self


class ReviewDecision(BaseModel):
    """Stored review (also read back from saved cards, so no request-time validation here)."""

    decision: Literal["accept", "edit", "request_info", "reassess"]
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


class FactChange(BaseModel):
    field: str
    before: str | float | bool | None
    after: str | float | bool | None


class ClaimCard(BaseModel):
    facts: ClaimFacts
    policy: PolicyContext
    coverage_status: CoverageStatus = "no_evidence"
    coverage_summary: str = ""
    coverage_uncertainty: CoverageUncertainty | None = None
    citations: list[Citation] = Field(default_factory=list)
    risk: RiskSignal | None = None
    risk_status: RiskStatus = "pending"
    risk_missing: list[str] = Field(default_factory=list)
    cost: CostContext | None = None
    missing_documents: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    status: ClaimStatus = "collecting"
    review: ReviewDecision | None = None
    assessment_stale: bool = False
    assessment_error: str | None = None
    corrections: list[FactChange] = Field(default_factory=list)

    @model_validator(mode="after")
    def _risk_availability(self):
        missing = missing_risk_inputs(self.facts, self.policy)
        if missing:
            self.risk = None
            self.risk_status = "insufficient_information"
            self.risk_missing = missing
        elif self.risk is not None:
            self.risk_status = "available"
            self.risk_missing = []
        elif self.risk_status == "available":
            self.risk_status = "unavailable"
        return self


class ComposeOutput(BaseModel):
    """Structured output of the compose step; validated against retrieved clauses before use."""

    answer: str = Field(
        description="Reply to the policyholder in their language, with [A.2.2.1.4]-style citations"
    )
    coverage_status: CoverageStatus
    coverage_uncertainty: CoverageUncertainty | None = None
    cited_clause_ids: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class FollowupOutput(BaseModel):
    question: str = Field(description="One friendly message asking for at most two missing facts")
    asked_for: list[str] = Field(default_factory=list, description="Field names being asked for")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
