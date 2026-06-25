from triage_service import reason_codes as rc
from triage_service.schemas import RiskLabel, ScoreBlock, TriageScoreRequest, TriageScoreResponse


SUPPORTED_REASON_CODES = {
    rc.HIGH_ESTIMATED_DAMAGE,
    rc.INJURY_REPORTED,
    rc.THIRD_PARTY_INVOLVED,
    rc.LATE_FNOL,
    rc.MISSING_POLICE_REPORT,
    rc.POLICY_RECENTLY_STARTED,
    rc.PRIOR_CLAIMS_HIGH,
    rc.LEGAL_KEYWORDS_DETECTED,
    rc.COVERAGE_LIMIT_EXCEEDED,
    rc.POLICY_NOT_ACTIVE_ON_LOSS_DATE,
    rc.COVERAGE_NOT_ACTIVE_ON_LOSS_DATE,
}


def score_triage(request: TriageScoreRequest) -> TriageScoreResponse:
    severity = _score_severity(request)
    fraud = _score_fraud(request)
    litigation = _score_litigation(request)
    recommended_queue = _recommended_queue(severity.label, fraud.label, litigation.label)
    human_review_required = (
        RiskLabel.HIGH in {severity.label, fraud.label, litigation.label}
        or not request.policy_features.coverage_valid
        or recommended_queue != "STANDARD_CLAIMS"
    )

    return TriageScoreResponse(
        claim_id=request.claim_id,
        claim_number=request.claim_number,
        severity=severity,
        fraud=fraud,
        litigation=litigation,
        recommended_queue=recommended_queue,
        human_review_required=human_review_required,
        explanation=_explanation(severity, fraud, litigation, recommended_queue),
    )


def _score_severity(request: TriageScoreRequest) -> ScoreBlock:
    score = 0.10
    reasons: list[str] = []
    claim = request.claim_features
    policy = request.policy_features

    if claim.estimated_loss_amount >= 25000:
        score += 0.45
        reasons.append(rc.HIGH_ESTIMATED_DAMAGE)
    elif claim.estimated_loss_amount >= 10000:
        score += 0.25

    if claim.injury_reported:
        score += 0.30
        reasons.append(rc.INJURY_REPORTED)

    if claim.third_party_involved:
        score += 0.15
        reasons.append(rc.THIRD_PARTY_INVOLVED)

    if claim.estimated_loss_amount > policy.coverage_limit_amount:
        score += 0.20
        reasons.append(rc.COVERAGE_LIMIT_EXCEEDED)

    return ScoreBlock(label=_label(score), score=round(min(score, 1.0), 4), reason_codes=reasons)


def _score_fraud(request: TriageScoreRequest) -> ScoreBlock:
    score = 0.05
    reasons: list[str] = []
    claim = request.claim_features
    policy = request.policy_features

    if policy.policy_age_days <= 30:
        score += 0.30
        reasons.append(rc.POLICY_RECENTLY_STARTED)

    if claim.loss_report_delay_days >= 21:
        score += 0.25
        reasons.append(rc.LATE_FNOL)

    if not claim.police_report_available and claim.claim_type.startswith("AUTO"):
        score += 0.20
        reasons.append(rc.MISSING_POLICE_REPORT)

    if claim.prior_claims_count >= 3:
        score += 0.20
        reasons.append(rc.PRIOR_CLAIMS_HIGH)

    if not policy.coverage_valid:
        score += 0.15
        reasons.extend(_known_reason_codes(policy.coverage_reasons))

    return ScoreBlock(label=_label(score), score=round(min(score, 1.0), 4), reason_codes=_dedupe(reasons))


def _score_litigation(request: TriageScoreRequest) -> ScoreBlock:
    score = 0.05
    reasons: list[str] = []
    text = request.text_features.loss_description.lower()

    if request.claim_features.injury_reported:
        score += 0.30
        reasons.append(rc.INJURY_REPORTED)

    if request.claim_features.third_party_involved:
        score += 0.15
        reasons.append(rc.THIRD_PARTY_INVOLVED)

    if any(keyword in text for keyword in ["attorney", "lawyer", "lawsuit", "legal", "sue"]):
        score += 0.35
        reasons.append(rc.LEGAL_KEYWORDS_DETECTED)

    return ScoreBlock(label=_label(score), score=round(min(score, 1.0), 4), reason_codes=_dedupe(reasons))


def _label(score: float) -> RiskLabel:
    if score >= 0.70:
        return RiskLabel.HIGH
    if score >= 0.35:
        return RiskLabel.MEDIUM
    return RiskLabel.LOW


def _recommended_queue(severity: RiskLabel, fraud: RiskLabel, litigation: RiskLabel) -> str:
    if fraud == RiskLabel.HIGH:
        return "SIU_REVIEW"
    if severity == RiskLabel.HIGH or litigation == RiskLabel.HIGH:
        return "COMPLEX_CLAIMS"
    return "STANDARD_CLAIMS"


def _explanation(severity: ScoreBlock, fraud: ScoreBlock, litigation: ScoreBlock, queue: str) -> str:
    return (
        f"Rule-based triage assigned severity={severity.label}, "
        f"fraudRisk={fraud.label}, litigationRisk={litigation.label}, queue={queue}. "
        "Signals are decision-support only and require human review for final claim decisions."
    )


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _known_reason_codes(values: list[str]) -> list[str]:
    return [value for value in values if value in SUPPORTED_REASON_CODES]
