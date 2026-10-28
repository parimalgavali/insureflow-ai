from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import MemorySaver

from api.agent.graph import AgentDeps, build_graph
from api.config import Settings
from api.llm.provider import RecordedProvider
from api.main import create_app
from api.state import AppState
from db.session import get_engine
from tests.agent_corpus import FakeScorer, make_retriever

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="needs Postgres (DATABASE_URL)"
)
FIXTURE = Path(__file__).parent / "fixtures" / "agent" / "hit_and_run.json"
MSG1 = "Gestern Abend hat jemand mein geparktes Auto auf dem Supermarktparkplatz in Köln angefahren und ist einfach weggefahren. Die hintere Stoßstange ist eingedrückt."
MSG2 = (
    "Das war am 25.10.2026 gegen 19 Uhr. Die Polizei habe ich nicht gerufen, Zeugen gab es keine."
)


def make_state(tmp_path: Path, token: str | None = None) -> AppState:
    settings = Settings(
        demo_api_token=token, upload_dir=tmp_path / "uploads", llm_provider="recorded"
    )
    provider = RecordedProvider(FIXTURE)
    deps = AgentDeps(
        provider=provider,
        retriever=make_retriever(),
        risk_scorer=FakeScorer(),
        today=lambda: "2026-10-26",
    )
    graph = build_graph(deps, checkpointer=MemorySaver())
    settings.upload_dir.mkdir(parents=True)
    return AppState(
        settings,
        get_engine(settings.database_url),
        graph,
        provider,
        deps.retriever,
        deps.risk_scorer,
    )


@pytest.fixture
def client(tmp_path: Path):
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config("alembic.ini"), "head")
    with TestClient(create_app(lambda: make_state(tmp_path))) as c:
        yield c


def parse_sse(body: str) -> list[tuple[str, dict]]:
    events = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line)
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def test_health(client: TestClient):
    body = client.get("/api/health").json()
    assert body["status"] == "ok" and body["db"] == "ok" and body["provider"] == "recorded"
    assert body["risk_model"] == "fake-0"


def test_full_conversation_flow(client: TestClient, tmp_path: Path):
    created = client.post(
        "/api/conversations",
        json={"language": "de", "policy": {"product": "vollkasko", "deductible_eur": 500}},
    )
    assert created.status_code == 201
    conv = created.json()
    cid, claim_id = conv["id"], conv["claim_id"]
    assert (
        conv["messages"][0]["role"] == "assistant"
        and "ClaimPilot" in conv["messages"][0]["content"]
    )

    r1 = client.post(f"/api/conversations/{cid}/messages", data={"text": MSG1})
    assert r1.status_code == 200 and r1.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(r1.text)
    kinds = [k for k, _ in events]
    assert kinds[0] == "facts" and "question" in kinds and kinds[-1] == "done"
    assert "token" in kinds and "card" not in kinds
    assert events[-1][1] == {"status": "collecting", "claim_id": claim_id, "awaiting_review": False}
    assert dict(events)["facts"]["facts"]["event_type"] == "hit_and_run"

    png = tmp_path / "bumper.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 100)
    with png.open("rb") as fh:
        r2 = client.post(
            f"/api/conversations/{cid}/messages",
            data={"text": MSG2},
            files={"file": ("bumper.png", fh, "image/png")},
        )
    events = parse_sse(r2.text)
    kinds = [k for k, _ in events]
    assert (
        kinds.index("facts")
        < kinds.index("citations")
        < kinds.index("risk")
        < kinds.index("token")
        < kinds.index("card")
        < kinds.index("done")
    )
    by_kind = dict(events)
    assert by_kind["risk"]["risk"]["band"] == "medium"
    assert {c["clause_id"] for c in by_kind["citations"]["citations"]} & {"A.2.2.2.2", "E.1.1.1"}
    assert by_kind["card"]["card"]["coverage_status"] == "likely_covered"
    assert by_kind["done"] == {
        "status": "awaiting_review",
        "claim_id": claim_id,
        "awaiting_review": True,
    }
    assert len(list((tmp_path / "uploads").rglob("*_bumper.png"))) == 1

    full = client.get(f"/api/conversations/{cid}").json()
    assert [m["role"] for m in full["messages"]] == [
        "assistant",
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert "[Attachment: bumper.png (image/png)]" in full["messages"][3]["content"]
    assert full["status"] == "awaiting_review" and full["card"]["facts"]["photos_attached"] is True
    assert full["policy"]["deductible_eur"] == 500

    blocked = client.post(f"/api/claims/{claim_id}/review", json={"decision": "accept"})
    assert blocked.status_code == 200
    reviewed = blocked.json()
    assert reviewed["status"] == "reviewed" and reviewed["card"]["review"]["decision"] == "accept"
    assert client.get(f"/api/claims/{claim_id}").json()["status"] == "reviewed"
    assert (
        client.post(f"/api/claims/{claim_id}/review", json={"decision": "accept"}).status_code
        == 409
    )
    assert (
        client.post(f"/api/conversations/{cid}/messages", data={"text": "noch was"}).status_code
        == 409
    )


def test_review_before_assessment_is_rejected(client: TestClient):
    conv = client.post("/api/conversations", json={}).json()
    assert (
        client.post(
            f"/api/claims/{conv['claim_id']}/review", json={"decision": "accept"}
        ).status_code
        == 409
    )
    assert client.get("/api/conversations/00000000-0000-0000-0000-000000000000").status_code == 404


def test_upload_type_rejected(client: TestClient):
    conv = client.post("/api/conversations", json={}).json()
    r = client.post(
        f"/api/conversations/{conv['id']}/messages",
        data={"text": "x"},
        files={"file": ("a.exe", b"MZ", "application/octet-stream")},
    )
    assert r.status_code == 415


def test_bearer_token_required_when_configured(tmp_path: Path):
    with TestClient(create_app(lambda: make_state(tmp_path, token="s3cret"))) as c:
        assert c.get("/api/health").status_code == 200  # health stays open
        assert c.post("/api/conversations", json={}).status_code == 401
        assert (
            c.post(
                "/api/conversations", json={}, headers={"Authorization": "Bearer wrong"}
            ).status_code
            == 401
        )
        assert (
            c.post(
                "/api/conversations", json={}, headers={"Authorization": "Bearer s3cret"}
            ).status_code
            == 201
        )
