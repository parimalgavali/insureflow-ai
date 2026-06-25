from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


Score = Annotated[float, Field(ge=0.0, le=1.0)]


class RiskLabel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PolicyFeatures(ApiModel):
    policy_type: str
    policy_age_days: int = Field(ge=0)
    coverage_limit_amount: float = Field(ge=0)
    deductible_amount: float = Field(ge=0)
    coverage_valid: bool = True
    coverage_reasons: list[str] = Field(default_factory=list)


class ClaimFeatures(ApiModel):
    claim_type: str
    estimated_loss_amount: float = Field(ge=0)
    injury_reported: bool = False
    third_party_involved: bool = False
    police_report_available: bool = False
    loss_report_delay_days: int = Field(ge=0)
    prior_claims_count: int = Field(ge=0)


class TextFeatures(ApiModel):
    loss_description: str = ""


class TriageScoreRequest(ApiModel):
    claim_id: str
    claim_number: str
    policy_features: PolicyFeatures
    claim_features: ClaimFeatures
    text_features: TextFeatures = Field(default_factory=TextFeatures)


class ScoreBlock(ApiModel):
    label: RiskLabel
    score: Score
    reason_codes: list[str]


class TriageScoreResponse(ApiModel):
    claim_id: str
    claim_number: str
    model_name: str = "rule-based-triage"
    model_version: str = "rules-v1"
    severity: ScoreBlock
    fraud: ScoreBlock
    litigation: ScoreBlock
    recommended_queue: str
    human_review_required: bool
    explanation: str
