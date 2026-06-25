# Phase 5 Rule-Based AI Triage Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explainable rule-based triage service that scores claims for severity, fraud risk, and litigation risk, then stores those decision-support signals in the claims workflow.

**Architecture:** Build the rules engine first as a small FastAPI service under `ai-services/triage-service`, with strict Pydantic request/response contracts and deterministic scoring. Integrate the Spring Boot claims API through a narrow triage client/service boundary, persist `ai_triage_results`, and add a claim timeline event when triage completes. Keep the rules transparent and audit-friendly so Phase 6 can replace or augment them with ML without changing the Java API contract.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic, pytest, Java 21, Spring Boot 3.3, Spring Web `RestClient`, Spring Data JPA, Bean Validation, Flyway, PostgreSQL, Testcontainers, JUnit 5, AssertJ.

---

## Branch

Use this branch:

```bash
rule-based-triage-service
```

## Agent Ownership

- **AI service agent:** Python FastAPI service, Pydantic schemas, deterministic scoring rules, Python tests.
- **Backend integration agent:** Java triage domain mapping, repository, client contract, service orchestration, API endpoint, integration tests.
- **Orchestrator:** shared contract review, docs, project memory, full verification, GitHub push/PR.

## Scope

Phase 5 is rules-first. Do not train ML models, download external ML datasets, call LLMs, or build frontend UI in this phase.

The service must call outputs "fraud risk" or "fraud risk level"; never call a claim fraudulent or confirmed fraud.

## File Map

### Create

- `ai-services/triage-service/pyproject.toml` - Python package metadata and test dependencies.
- `ai-services/triage-service/README.md` - local run, API contract, and responsible AI note.
- `ai-services/triage-service/triage_service/__init__.py` - package marker.
- `ai-services/triage-service/triage_service/schemas.py` - Pydantic request/response models.
- `ai-services/triage-service/triage_service/reason_codes.py` - centralized reason-code constants.
- `ai-services/triage-service/triage_service/rules.py` - deterministic severity, fraud, and litigation scoring.
- `ai-services/triage-service/triage_service/app.py` - FastAPI app with health and score endpoints.
- `ai-services/triage-service/tests/test_rules.py` - rule scoring tests.
- `ai-services/triage-service/tests/test_api.py` - FastAPI contract tests.
- `backend/api/src/main/java/com/insureflow/api/ai/triage/api/ClaimTriageController.java` - backend claim triage endpoint.
- `backend/api/src/main/java/com/insureflow/api/ai/triage/api/dto/*.java` - backend triage request/response DTO records.
- `backend/api/src/main/java/com/insureflow/api/ai/triage/client/*.java` - triage client interface and RestClient implementation.
- `backend/api/src/main/java/com/insureflow/api/ai/triage/config/AiTriageProperties.java` - AI service base URL and version configuration.
- `backend/api/src/main/java/com/insureflow/api/ai/triage/domain/*.java` - triage entity and label enums.
- `backend/api/src/main/java/com/insureflow/api/ai/triage/repository/AiTriageResultRepository.java` - persisted result repository.
- `backend/api/src/main/java/com/insureflow/api/ai/triage/service/*.java` - feature assembler and orchestration service.
- `backend/api/src/main/resources/db/migration/V3__ai_triage_result_contract.sql` - adds label/version columns and result indexes.
- `backend/api/src/test/java/com/insureflow/api/ai/triage/*.java` - backend triage integration/repository/client tests.
- `docs/api/ai-triage.md` - Phase 5 API and rule behavior guide.

### Modify

- `backend/api/src/main/java/com/insureflow/api/claims/domain/ClaimEventType.java` - add `TRIAGE_COMPLETED`.
- `backend/api/src/test/java/com/insureflow/api/database/FlywayMigrationTest.java` - verify updated `ai_triage_results` contract.
- `scripts/run-tests.sh` - include the triage service Python tests.
- `README.md` - add the Phase 5 local test command and service summary.
- `docs/README.md` - link the triage API guide.
- `PROJECT_MEMORY.md` - record branch creation, plan creation, implementation completion, and verification.

## API Contract

Python service endpoint:

```text
POST /ai/v1/triage/score
```

Backend endpoint:

```text
POST /api/v1/claims/{claimNumber}/triage
GET /api/v1/claims/{claimNumber}/triage
```

The backend `POST` endpoint triggers scoring, persists the result, records a timeline event, and returns the stored response. The backend `GET` endpoint returns the latest stored triage result for the claim.

## Rule Labels

Use these labels:

- `LOW`
- `MEDIUM`
- `HIGH`

Use score range `0.0000` to `1.0000`.

## Reason Codes

Use this central list in Python and mirror it in backend tests/docs:

```text
HIGH_ESTIMATED_DAMAGE
INJURY_REPORTED
THIRD_PARTY_INVOLVED
LATE_FNOL
MISSING_POLICE_REPORT
POLICY_RECENTLY_STARTED
PRIOR_CLAIMS_HIGH
LEGAL_KEYWORDS_DETECTED
COVERAGE_LIMIT_EXCEEDED
POLICY_NOT_ACTIVE_ON_LOSS_DATE
COVERAGE_NOT_ACTIVE_ON_LOSS_DATE
```

## Recommended Queue Rules

- `SIU_REVIEW` when fraud risk is `HIGH`.
- `COMPLEX_CLAIMS` when severity is `HIGH` or litigation risk is `HIGH`.
- `STANDARD_CLAIMS` otherwise.

`humanReviewRequired` is true when any risk label is `HIGH`, coverage validation is not covered, or recommended queue is not `STANDARD_CLAIMS`.

---

## Task 1: Python Triage Service Foundation

**Files:**
- Create: `ai-services/triage-service/pyproject.toml`
- Create: `ai-services/triage-service/README.md`
- Create: `ai-services/triage-service/triage_service/__init__.py`
- Create: `ai-services/triage-service/triage_service/schemas.py`
- Test: `ai-services/triage-service/tests/test_api.py`

- [ ] **Step 1: Write failing schema/API import test**

Create `tests/test_api.py`:

```python
from fastapi.testclient import TestClient

from triage_service.app import app


def test_health_endpoint():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "triage-service"}
```

- [ ] **Step 2: Run test and verify it fails**

```bash
cd ai-services/triage-service
python3 -m pytest tests/test_api.py -q
```

Expected: FAIL because `triage_service.app` does not exist.

- [ ] **Step 3: Add package metadata**

Create `pyproject.toml`:

```toml
[project]
name = "insureflow-triage-service"
version = "0.1.0"
description = "Rule-based AI triage service for InsureFlow AI"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115.0",
  "pydantic>=2.8.0",
  "uvicorn>=0.30.0",
]

[project.optional-dependencies]
test = [
  "httpx>=0.27.0",
  "pytest>=8.0.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 4: Add initial schemas**

Create `triage_service/schemas.py`:

```python
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
```

- [ ] **Step 5: Add FastAPI app**

Create `triage_service/app.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="InsureFlow AI Triage Service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "triage-service"}
```

- [ ] **Step 6: Verify and commit**

```bash
cd ai-services/triage-service
python3 -m pytest tests/test_api.py -q
cd ../..
git add ai-services/triage-service
git commit -m "feat: add triage service foundation"
```

Expected: `1 passed`.

## Task 2: Deterministic Scoring Rules

**Files:**
- Create: `ai-services/triage-service/triage_service/reason_codes.py`
- Create: `ai-services/triage-service/triage_service/rules.py`
- Modify: `ai-services/triage-service/triage_service/app.py`
- Test: `ai-services/triage-service/tests/test_rules.py`
- Test: `ai-services/triage-service/tests/test_api.py`

- [ ] **Step 1: Write failing rule tests**

Create `tests/test_rules.py`:

```python
from triage_service.rules import score_triage
from triage_service.schemas import (
    ClaimFeatures,
    PolicyFeatures,
    TextFeatures,
    TriageScoreRequest,
)


def make_request(**overrides):
    claim = {
        "claim_type": "AUTO_COLLISION",
        "estimated_loss_amount": 9000.0,
        "injury_reported": False,
        "third_party_involved": False,
        "police_report_available": True,
        "loss_report_delay_days": 2,
        "prior_claims_count": 0,
    }
    claim.update(overrides)
    return TriageScoreRequest(
        claim_id="11111111-1111-1111-1111-111111111111",
        claim_number="CLM-20260625-000001",
        policy_features=PolicyFeatures(
            policy_type="PERSONAL_AUTO",
            policy_age_days=120,
            coverage_limit_amount=25000.0,
            deductible_amount=500.0,
            coverage_valid=True,
            coverage_reasons=[],
        ),
        claim_features=ClaimFeatures(**claim),
        text_features=TextFeatures(loss_description="Rear-end collision at a stop light."),
    )


def test_high_severity_for_injury_and_large_loss():
    result = score_triage(make_request(estimated_loss_amount=45000.0, injury_reported=True))

    assert result.severity.label == "HIGH"
    assert "HIGH_ESTIMATED_DAMAGE" in result.severity.reason_codes
    assert "INJURY_REPORTED" in result.severity.reason_codes
    assert result.recommended_queue == "COMPLEX_CLAIMS"


def test_high_fraud_risk_for_recent_policy_late_fnol_and_missing_police_report():
    request = make_request(
        police_report_available=False,
        loss_report_delay_days=30,
        prior_claims_count=3,
    )
    request.policy_features.policy_age_days = 10

    result = score_triage(request)

    assert result.fraud.label == "HIGH"
    assert result.recommended_queue == "SIU_REVIEW"
    assert "POLICY_RECENTLY_STARTED" in result.fraud.reason_codes
    assert "LATE_FNOL" in result.fraud.reason_codes
    assert "MISSING_POLICE_REPORT" in result.fraud.reason_codes


def test_litigation_risk_for_legal_keywords():
    result = score_triage(make_request(injury_reported=True))
    request_with_legal_text = make_request(injury_reported=True)
    request_with_legal_text.text_features.loss_description = "Customer says an attorney may file a lawsuit."
    result_with_legal_text = score_triage(request_with_legal_text)

    assert result.litigation.label in {"LOW", "MEDIUM"}
    assert result_with_legal_text.litigation.label == "HIGH"
    assert "LEGAL_KEYWORDS_DETECTED" in result_with_legal_text.litigation.reason_codes
```

- [ ] **Step 2: Run test and verify it fails**

```bash
cd ai-services/triage-service
python3 -m pytest tests/test_rules.py -q
```

Expected: FAIL because `triage_service.rules` does not exist.

- [ ] **Step 3: Add reason codes**

Create `triage_service/reason_codes.py`:

```python
HIGH_ESTIMATED_DAMAGE = "HIGH_ESTIMATED_DAMAGE"
INJURY_REPORTED = "INJURY_REPORTED"
THIRD_PARTY_INVOLVED = "THIRD_PARTY_INVOLVED"
LATE_FNOL = "LATE_FNOL"
MISSING_POLICE_REPORT = "MISSING_POLICE_REPORT"
POLICY_RECENTLY_STARTED = "POLICY_RECENTLY_STARTED"
PRIOR_CLAIMS_HIGH = "PRIOR_CLAIMS_HIGH"
LEGAL_KEYWORDS_DETECTED = "LEGAL_KEYWORDS_DETECTED"
COVERAGE_LIMIT_EXCEEDED = "COVERAGE_LIMIT_EXCEEDED"
POLICY_NOT_ACTIVE_ON_LOSS_DATE = "POLICY_NOT_ACTIVE_ON_LOSS_DATE"
COVERAGE_NOT_ACTIVE_ON_LOSS_DATE = "COVERAGE_NOT_ACTIVE_ON_LOSS_DATE"
```

- [ ] **Step 4: Add scoring implementation**

Create `triage_service/rules.py`:

```python
from triage_service import reason_codes as rc
from triage_service.schemas import RiskLabel, ScoreBlock, TriageScoreRequest, TriageScoreResponse


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

    if policy.coverage_limit_amount and claim.estimated_loss_amount > policy.coverage_limit_amount:
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
        reasons.extend(policy.coverage_reasons)

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
```

- [ ] **Step 5: Add score endpoint**

Modify `triage_service/app.py`:

```python
from fastapi import FastAPI

from triage_service.rules import score_triage
from triage_service.schemas import TriageScoreRequest, TriageScoreResponse

app = FastAPI(title="InsureFlow AI Triage Service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "triage-service"}


@app.post("/ai/v1/triage/score", response_model=TriageScoreResponse)
def score(request: TriageScoreRequest) -> TriageScoreResponse:
    return score_triage(request)
```

- [ ] **Step 6: Add API contract test**

Extend `tests/test_api.py`:

```python
def test_score_endpoint_returns_rule_based_triage():
    client = TestClient(app)

    response = client.post(
        "/ai/v1/triage/score",
        json={
            "claim_id": "11111111-1111-1111-1111-111111111111",
            "claim_number": "CLM-20260625-000001",
            "policy_features": {
                "policy_type": "PERSONAL_AUTO",
                "policy_age_days": 12,
                "coverage_limit_amount": 25000.0,
                "deductible_amount": 500.0,
                "coverage_valid": True,
                "coverage_reasons": [],
            },
            "claim_features": {
                "claim_type": "AUTO_COLLISION",
                "estimated_loss_amount": 30000.0,
                "injury_reported": True,
                "third_party_involved": True,
                "police_report_available": False,
                "loss_report_delay_days": 25,
                "prior_claims_count": 0,
            },
            "text_features": {"loss_description": "Attorney contacted after injury collision."},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["modelVersion"] == "rules-v1"
    assert body["severity"]["label"] == "HIGH"
    assert body["fraud"]["label"] in {"MEDIUM", "HIGH"}
    assert body["humanReviewRequired"] is True
```

- [ ] **Step 7: Verify and commit**

```bash
cd ai-services/triage-service
python3 -m pytest -q
cd ../..
git add ai-services/triage-service
git commit -m "feat: add rule-based triage scoring"
```

Expected: all triage service tests pass.

## Task 3: Backend Triage Persistence Contract

**Files:**
- Create: `backend/api/src/main/java/com/insureflow/api/ai/triage/domain/TriageRiskLabel.java`
- Create: `backend/api/src/main/java/com/insureflow/api/ai/triage/domain/AiTriageResult.java`
- Create: `backend/api/src/main/java/com/insureflow/api/ai/triage/repository/AiTriageResultRepository.java`
- Create: `backend/api/src/main/resources/db/migration/V3__ai_triage_result_contract.sql`
- Test: `backend/api/src/test/java/com/insureflow/api/ai/triage/AiTriageResultRepositoryTest.java`
- Modify: `backend/api/src/test/java/com/insureflow/api/database/FlywayMigrationTest.java`

- [ ] **Step 1: Write failing repository test**

Create `AiTriageResultRepositoryTest` that saves a customer, policy, claim, and triage result, then verifies the latest result is returned for a claim number.

- [ ] **Step 2: Run test and verify it fails**

```bash
cd backend
mvn -pl api test -Dtest=AiTriageResultRepositoryTest
```

Expected: compilation fails because triage domain/repository classes do not exist.

- [ ] **Step 3: Add V3 migration**

Create `V3__ai_triage_result_contract.sql`:

```sql
ALTER TABLE ai_triage_results
    ADD COLUMN model_name VARCHAR(120) NOT NULL DEFAULT 'rule-based-triage',
    ADD COLUMN model_version VARCHAR(80) NOT NULL DEFAULT 'rules-v1',
    ADD COLUMN severity_label VARCHAR(40) NOT NULL DEFAULT 'LOW',
    ADD COLUMN fraud_risk_label VARCHAR(40) NOT NULL DEFAULT 'LOW',
    ADD COLUMN litigation_risk_label VARCHAR(40) NOT NULL DEFAULT 'LOW',
    ADD COLUMN human_review_required BOOLEAN NOT NULL DEFAULT false;

CREATE INDEX idx_ai_triage_results_claim_id_created_at
    ON ai_triage_results(claim_id, created_at DESC);
```

- [ ] **Step 4: Implement triage entity and repository**

Create enum `TriageRiskLabel` with `LOW`, `MEDIUM`, `HIGH`.

Map `AiTriageResult` to `ai_triage_results` with fields:

```java
Claim claim;
String modelName;
String modelVersion;
BigDecimal severityScore;
TriageRiskLabel severityLabel;
BigDecimal fraudRiskScore;
TriageRiskLabel fraudRiskLabel;
BigDecimal litigationRiskScore;
TriageRiskLabel litigationRiskLabel;
String recommendedQueue;
String reasonCodes;
String explanation;
boolean humanReviewRequired;
```

Use `@JdbcTypeCode(SqlTypes.JSON)` for `reasonCodes` as `List<String>` if consistent with existing `ClaimEvent.payload`; otherwise map as `String` JSON and convert in DTOs. Prefer `List<String>` if Hibernate handles the JSON column cleanly in repository tests.

Repository method:

```java
List<AiTriageResult> findByClaimClaimNumberOrderByCreatedAtDesc(String claimNumber);
```

- [ ] **Step 5: Update migration smoke test**

Update `FlywayMigrationTest` to keep verifying `ai_triage_results` exists after V3 migrations apply.

- [ ] **Step 6: Verify and commit**

```bash
cd backend
mvn -pl api test -Dtest=AiTriageResultRepositoryTest,FlywayMigrationTest
git add backend/api/src/main/java/com/insureflow/api/ai/triage/domain backend/api/src/main/java/com/insureflow/api/ai/triage/repository backend/api/src/main/resources/db/migration/V3__ai_triage_result_contract.sql backend/api/src/test/java/com/insureflow/api/ai/triage backend/api/src/test/java/com/insureflow/api/database
git commit -m "feat: persist ai triage results"
```

## Task 4: Backend Triage Client Contract

**Files:**
- Create: `backend/api/src/main/java/com/insureflow/api/ai/triage/api/dto/TriageScoreRequest.java`
- Create: `backend/api/src/main/java/com/insureflow/api/ai/triage/api/dto/TriageScoreResponse.java`
- Create: `backend/api/src/main/java/com/insureflow/api/ai/triage/api/dto/TriageScoreBlock.java`
- Create: `backend/api/src/main/java/com/insureflow/api/ai/triage/client/TriageClient.java`
- Create: `backend/api/src/main/java/com/insureflow/api/ai/triage/client/RestTriageClient.java`
- Create: `backend/api/src/main/java/com/insureflow/api/ai/triage/config/AiTriageProperties.java`
- Test: `backend/api/src/test/java/com/insureflow/api/ai/triage/RestTriageClientTest.java`
- Modify: `backend/api/src/main/java/com/insureflow/api/InsureFlowApiApplication.java`
- Modify: `backend/api/src/main/resources/application.yml`

- [ ] **Step 1: Write failing client test**

Use `MockRestServiceServer` with a `RestClient.Builder` to verify the client sends `POST /ai/v1/triage/score` and parses severity/fraud/litigation response fields.

- [ ] **Step 2: Run test and verify it fails**

```bash
cd backend
mvn -pl api test -Dtest=RestTriageClientTest
```

Expected: compilation fails because client classes do not exist.

- [ ] **Step 3: Add configuration properties**

Create `AiTriageProperties`:

```java
@ConfigurationProperties(prefix = "insureflow.ai.triage")
public record AiTriageProperties(String baseUrl) {
    public AiTriageProperties {
        if (baseUrl == null || baseUrl.isBlank()) {
            baseUrl = "http://localhost:8001";
        }
    }
}
```

Enable configuration properties in `InsureFlowApiApplication`.

Add to `application.yml`:

```yaml
insureflow:
  ai:
    triage:
      base-url: http://localhost:8001
```

- [ ] **Step 4: Add DTO records and client**

Implement DTOs matching the Python JSON contract. Use Java record component names that serialize to snake_case if the project config supports it; otherwise annotate with `@JsonProperty`.

Implement:

```java
public interface TriageClient {
    TriageScoreResponse score(TriageScoreRequest request);
}
```

`RestTriageClient` should use `RestClient`:

```java
return restClient.post()
        .uri("/ai/v1/triage/score")
        .body(request)
        .retrieve()
        .body(TriageScoreResponse.class);
```

If the AI service returns no body, throw `BusinessRuleViolationException("AI triage service returned an empty response")`.

- [ ] **Step 5: Verify and commit**

```bash
cd backend
mvn -pl api test -Dtest=RestTriageClientTest
git add backend/api/src/main/java/com/insureflow/api/ai/triage/api/dto backend/api/src/main/java/com/insureflow/api/ai/triage/client backend/api/src/main/java/com/insureflow/api/ai/triage/config backend/api/src/main/java/com/insureflow/api/InsureFlowApiApplication.java backend/api/src/main/resources/application.yml backend/api/src/test/java/com/insureflow/api/ai/triage
git commit -m "feat: add ai triage client contract"
```

## Task 5: Backend Claim Feature Assembly And Triage API

**Files:**
- Create: `backend/api/src/main/java/com/insureflow/api/ai/triage/service/ClaimTriageFeatureAssembler.java`
- Create: `backend/api/src/main/java/com/insureflow/api/ai/triage/service/ClaimTriageService.java`
- Create: `backend/api/src/main/java/com/insureflow/api/ai/triage/api/ClaimTriageController.java`
- Create: `backend/api/src/main/java/com/insureflow/api/ai/triage/api/dto/ClaimTriageResponse.java`
- Modify: `backend/api/src/main/java/com/insureflow/api/claims/domain/ClaimEventType.java`
- Test: `backend/api/src/test/java/com/insureflow/api/ai/triage/ClaimTriageIntegrationTest.java`

- [ ] **Step 1: Write failing integration test**

Create a Spring Boot integration test that:

1. Creates customer, policy, coverage, and a submitted claim through existing APIs.
2. Uses a test `@Primary` implementation of `TriageClient` returning a deterministic high-severity response.
3. Calls `POST /api/v1/claims/{claimNumber}/triage`.
4. Asserts response contains `severityLabel=HIGH`, `recommendedQueue=COMPLEX_CLAIMS`, and `humanReviewRequired=true`.
5. Calls `GET /api/v1/claims/{claimNumber}/events` and verifies a `TRIAGE_COMPLETED` event exists.
6. Calls `GET /api/v1/claims/{claimNumber}/triage` and verifies the persisted latest result is returned.

- [ ] **Step 2: Run test and verify it fails**

```bash
cd backend
mvn -pl api test -Dtest=ClaimTriageIntegrationTest
```

Expected: compilation fails because triage API/service classes do not exist.

- [ ] **Step 3: Add timeline event type**

Add `TRIAGE_COMPLETED` to `ClaimEventType`.

- [ ] **Step 4: Implement feature assembler**

`ClaimTriageFeatureAssembler` should assemble:

- claim id and claim number.
- policy type.
- policy age in days between policy effective date and claim loss date, minimum `0`.
- coverage limit and deductible from matching claim coverage when available.
- coverage valid and coverage reasons from latest claim coverage snapshot when available.
- estimated loss amount.
- injury flag from description keywords: `injury`, `injured`, `medical`, `ambulance`, `hospital`.
- third-party flag from description keywords: `third party`, `other driver`, `pedestrian`, `passenger`.
- police report availability from claim document metadata when any document type is `POLICE_REPORT`.
- FNOL delay in days between loss date and reported timestamp date.
- prior claims count for the same customer before the current claim.
- loss description.

- [ ] **Step 5: Implement triage orchestration**

`ClaimTriageService.runTriage(claimNumber)` should:

1. Find the claim or throw `ResourceNotFoundException`.
2. Assemble `TriageScoreRequest`.
3. Call `TriageClient.score`.
4. Persist `AiTriageResult`.
5. Record `TRIAGE_COMPLETED` timeline event with labels, scores, queue, and reason codes.
6. Return `ClaimTriageResponse`.

`ClaimTriageService.getLatestTriage(claimNumber)` should return the latest persisted result or throw `ResourceNotFoundException("No triage result found for claim " + claimNumber)`.

- [ ] **Step 6: Add controller**

Add:

```java
@PostMapping("/claims/{claimNumber}/triage")
ResponseEntity<ClaimTriageResponse> runTriage(@PathVariable String claimNumber)
```

and:

```java
@GetMapping("/claims/{claimNumber}/triage")
ClaimTriageResponse getLatestTriage(@PathVariable String claimNumber)
```

- [ ] **Step 7: Verify and commit**

```bash
cd backend
mvn -pl api test -Dtest=ClaimTriageIntegrationTest
git add backend/api/src/main/java/com/insureflow/api/ai/triage backend/api/src/main/java/com/insureflow/api/claims/domain/ClaimEventType.java backend/api/src/test/java/com/insureflow/api/ai/triage
git commit -m "feat: integrate claim triage workflow"
```

## Task 6: Failure Handling And Contract Guardrails

**Files:**
- Modify: `backend/api/src/main/java/com/insureflow/api/ai/triage/client/RestTriageClient.java`
- Modify: `backend/api/src/main/java/com/insureflow/api/shared/api/ApiExceptionHandler.java`
- Test: `backend/api/src/test/java/com/insureflow/api/ai/triage/ClaimTriageFailureIntegrationTest.java`

- [ ] **Step 1: Write failing service-unavailable test**

Create a test `TriageClient` bean that throws `ResourceAccessException("connection refused")`. Call `POST /api/v1/claims/{claimNumber}/triage` and expect HTTP 503 with message containing `AI triage service unavailable`.

- [ ] **Step 2: Run test and verify it fails**

```bash
cd backend
mvn -pl api test -Dtest=ClaimTriageFailureIntegrationTest
```

Expected: fails because triage client failures are not mapped yet.

- [ ] **Step 3: Add exception and handler**

Create `AiServiceUnavailableException` or reuse a shared exception if one exists. Map it to HTTP 503 in `ApiExceptionHandler`.

Wrap `RestClientException` in `RestTriageClient`:

```java
catch (RestClientException exception) {
    throw new AiServiceUnavailableException("AI triage service unavailable", exception);
}
```

- [ ] **Step 4: Verify and commit**

```bash
cd backend
mvn -pl api test -Dtest=ClaimTriageFailureIntegrationTest,RestTriageClientTest
git add backend/api/src/main/java/com/insureflow/api/ai/triage backend/api/src/main/java/com/insureflow/api/shared backend/api/src/test/java/com/insureflow/api/ai/triage
git commit -m "feat: handle ai triage service failures"
```

## Task 7: Scripts, Docs, Memory, And Full Verification

**Files:**
- Modify: `scripts/run-tests.sh`
- Modify: `README.md`
- Modify: `docs/README.md`
- Create: `docs/api/ai-triage.md`
- Modify: `PROJECT_MEMORY.md`

- [ ] **Step 1: Update full test script**

Add after synthetic generator tests:

```bash
(
  cd ai-services/triage-service
  python3 -m pytest -q
)
```

- [ ] **Step 2: Add triage API docs**

Create `docs/api/ai-triage.md` covering:

- How to run the Python service.
- Python endpoint `POST /ai/v1/triage/score`.
- Backend endpoints `POST /claims/{claimNumber}/triage` and `GET /claims/{claimNumber}/triage`.
- Reason codes.
- Responsible AI wording: decision-support only, no automatic claim denial, no fraud accusation.
- Demo sequence after FNOL.

- [ ] **Step 3: Update README and docs index**

Add Phase 5 to README feature progress and link `docs/api/ai-triage.md` from `docs/README.md`.

- [ ] **Step 4: Update project memory**

Record:

- Branch `rule-based-triage-service`.
- Phase 5 plan and implementation started.
- New AI triage service contract.
- Verification result after full tests pass.

- [ ] **Step 5: Run full verification**

```bash
./scripts/run-tests.sh
git diff --check
```

Expected:

- Backend tests pass.
- Synthetic generator tests pass.
- Triage service Python tests pass.
- `git diff --check` produces no output.

- [ ] **Step 6: Commit and push**

```bash
git add scripts/run-tests.sh README.md docs/README.md docs/api/ai-triage.md PROJECT_MEMORY.md
git commit -m "docs: document ai triage workflow"
git push -u origin rule-based-triage-service
```

## Review Checklist

- [ ] Python and Java triage contracts use the same field meanings.
- [ ] Fraud output is always phrased as risk, never confirmed fraud.
- [ ] Triage results include scores, labels, reason codes, queue, explanation, and human review flag.
- [ ] Backend stores triage results in PostgreSQL.
- [ ] Timeline includes `TRIAGE_COMPLETED`.
- [ ] AI service outage returns 503, not 500.
- [ ] `./scripts/run-tests.sh` includes backend, synthetic data generator, and triage service tests.
- [ ] `PROJECT_MEMORY.md` is updated.
