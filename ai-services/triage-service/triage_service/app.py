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
