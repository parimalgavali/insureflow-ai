from __future__ import annotations

import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
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


ADJUSTER_TOKEN = "adj-s3cret"
ADJUSTER = {"Authorization": f"Bearer {ADJUSTER_TOKEN}"}


def make_state(
    tmp_path: Path,
    token: str | None = None,
    adjuster_token: str | None = ADJUSTER_TOKEN,
    allow_open_api: bool = True,
    fixture: Path = FIXTURE,
) -> AppState:
    settings = Settings(
        demo_api_token=token,
        adjuster_api_token=adjuster_token,
        allow_open_api=allow_open_api,
        upload_dir=tmp_path / "uploads",
        llm_provider="recorded",
    )
    provider = RecordedProvider(fixture)
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
def client(tmp_path: Path, request):
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config("alembic.ini"), "head")
    with TestClient(
        create_app(lambda: make_state(tmp_path, fixture=getattr(request, "param", FIXTURE)))
    ) as c:
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
        "status": "assessed",
        "claim_id": claim_id,
        "awaiting_review": False,
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
    assert full["status"] == "assessed" and full["card"]["facts"]["photos_attached"] is True
    assert full["policy"]["deductible_eur"] == 500

    review_url = f"/api/claims/{claim_id}/review"
    assert client.post(review_url, json={"decision": "accept"}, headers=ADJUSTER).status_code == 409
    assert (
        client.post(f"/api/conversations/{cid}/messages", data={"text": "extra"}).status_code == 409
    )
    submit_url = f"/api/claims/{claim_id}/submit"
    with ThreadPoolExecutor(max_workers=2) as pool:
        submissions = list(pool.map(lambda _: client.post(submit_url), range(2)))
    submitted = submissions[0]
    assert submitted.status_code == 200
    assert submissions[1].status_code == 200
    assert submissions[1].json() == submitted.json()
    assert submitted.json()["status"] == "awaiting_review"
    assert submitted.json()["card"]["review"] is None
    assert datetime.fromisoformat(submitted.json()["submitted_at"]).tzinfo is not None
    assert client.post(submit_url).json() == submitted.json()
    assert client.get(f"/api/conversations/{cid}").json()["status"] == "awaiting_review"
    assert len(client.get(f"/api/conversations/{cid}").json()["messages"]) == len(full["messages"])

    assert client.post(review_url, json={"decision": "accept"}).status_code == 401
    assert (
        client.post(
            review_url, json={"decision": "accept"}, headers={"Authorization": "Bearer nope"}
        ).status_code
        == 403
    )
    for bad in (
        {"decision": "accept", "reviewer": "senior adjuster"},
        {"decision": "edit", "facts_patch": {"fraud_score": 0}},
        {"decision": "edit", "facts_patch": {"estimated_amount_eur": "a lot"}},
    ):
        assert client.post(review_url, json=bad, headers=ADJUSTER).status_code == 422
    assert client.get(f"/api/claims/{claim_id}").json()["status"] == "awaiting_review"

    blocked = client.post(
        review_url,
        json={"decision": "edit", "facts_patch": {"witnesses": True}},
        headers=ADJUSTER,
    )
    assert blocked.status_code == 200
    reviewed = blocked.json()
    assert reviewed["status"] == "reviewed" and reviewed["card"]["review"]["decision"] == "edit"
    assert reviewed["card"]["review"]["reviewer"] == "adjuster"
    assert reviewed["card"]["facts"]["witnesses"] is True
    assert client.get(f"/api/claims/{claim_id}").json()["status"] == "reviewed"
    assert client.post(review_url, json={"decision": "accept"}, headers=ADJUSTER).status_code == 409
    assert client.post(submit_url).json() == reviewed
    assert (
        client.post(f"/api/conversations/{cid}/messages", data={"text": "noch was"}).status_code
        == 409
    )


def test_review_before_assessment_is_rejected(client: TestClient):
    conv = client.post("/api/conversations", json={}).json()
    assert (
        client.post(
            f"/api/claims/{conv['claim_id']}/review", json={"decision": "accept"}, headers=ADJUSTER
        ).status_code
        == 409
    )
    assert client.post(f"/api/claims/{conv['claim_id']}/submit").status_code == 409
    assert client.post("/api/claims/00000000-0000-0000-0000-000000000000/submit").status_code == 404
    assert client.get("/api/conversations/00000000-0000-0000-0000-000000000000").status_code == 404


@pytest.mark.parametrize("client", [FIXTURE.with_name("hit_and_run_followup.json")], indirect=True)
def test_request_information_reply_and_resubmit(client: TestClient):
    conv = client.post("/api/conversations", json={"language": "en"}).json()
    cid, claim_id = conv["id"], conv["claim_id"]
    client.post(f"/api/conversations/{cid}/messages", data={"text": MSG1})
    client.post(f"/api/conversations/{cid}/messages", data={"text": MSG2})
    first_submission = client.post(f"/api/claims/{claim_id}/submit").json()
    url = f"/api/claims/{claim_id}/review"
    for note in (None, " ", "x" * 2001):
        assert (
            client.post(
                url, json={"decision": "request_info", "note": note}, headers=ADJUSTER
            ).status_code
            == 422
        )
    body = {
        "decision": "request_info",
        "note": "Please provide the police report and repair estimate.",
    }
    assert client.post(url, json=body).status_code == 401
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(lambda _: client.post(url, json=body, headers=ADJUSTER), range(2))
        )
    assert sorted(r.status_code for r in responses) == [200, 409]
    result = next(r.json() for r in responses if r.status_code == 200)
    assert result["status"] == "information_needed"
    assert result["card"]["review"]["decision"] == "request_info"
    saved = client.get(f"/api/conversations/{cid}").json()
    assert saved["status"] == saved["card"]["status"] == "information_needed"
    assert sum(body["note"] in m["content"] for m in saved["messages"]) == 1
    assert client.post(f"/api/claims/{claim_id}/submit").status_code == 409
    pending = client.get("/api/claims/review-queue?limit=100", headers=ADJUSTER).json()["items"]
    assert claim_id not in {i["id"] for i in pending}
    reply = client.post(
        f"/api/conversations/{cid}/messages",
        data={"text": "The police have now been informed. The repair estimate is 1200 Euro."},
    )
    assert dict(parse_sse(reply.text))["done"]["status"] == "assessed"
    updated = client.get(f"/api/conversations/{cid}").json()
    assert updated["card"]["facts"]["police_report_filed"] is True
    assert updated["card"]["review"] is None
    assert client.post(url, json={"decision": "accept"}, headers=ADJUSTER).status_code == 409
    submitted = client.post(f"/api/claims/{claim_id}/submit").json()
    assert submitted["submitted_at"] > first_submission["submitted_at"]
    assert submitted["status"] == "awaiting_review"
    assert (
        client.post(url, json={"decision": "accept"}, headers=ADJUSTER).json()["status"]
        == "reviewed"
    )


@pytest.mark.parametrize("client", [FIXTURE.with_name("hit_and_run_followup.json")], indirect=True)
def test_information_request_recovers_after_claim_commit_failure(client, monkeypatch):
    from sqlalchemy.orm import Session

    conv = client.post("/api/conversations", json={}).json()
    cid, claim_id = conv["id"], conv["claim_id"]
    client.post(f"/api/conversations/{cid}/messages", data={"text": MSG1})
    client.post(f"/api/conversations/{cid}/messages", data={"text": MSG2})
    client.post(f"/api/claims/{claim_id}/submit")
    url = f"/api/claims/{claim_id}/review"
    body = {"decision": "request_info", "note": "Police report please"}

    def fail_commit(_session):
        raise RuntimeError("simulated database failure")

    with monkeypatch.context() as patch:
        patch.setattr(Session, "commit", fail_commit)
        with pytest.raises(RuntimeError, match="simulated database failure"):
            client.post(url, json=body, headers=ADJUSTER)
    assert client.get(f"/api/claims/{claim_id}").json()["status"] == "awaiting_review"
    assert (
        client.post(
            url, json={"decision": "request_info", "note": "A different request"}, headers=ADJUSTER
        ).status_code
        == 409
    )
    recovered = client.post(url, json=body, headers=ADJUSTER)
    assert recovered.status_code == 200 and recovered.json()["status"] == "information_needed"
    saved = client.get(f"/api/conversations/{cid}").json()
    assert sum(body["note"] in m["content"] for m in saved["messages"]) == 1


def test_reviewer_queue_is_protected_and_lists_pending_claims(client, tmp_path):
    from api.agent.schemas import Citation, ClaimCard, ClaimFacts, PolicyContext, RiskSignal
    from db.models import Claim, Conversation

    state = make_state(tmp_path / "queue", token="customer-token")
    ids = {}
    with state.session() as session:
        for index, status in enumerate(
            ("awaiting_review", "awaiting_review", "collecting", "reviewed")
        ):
            conv = Conversation(status=status)
            card = ClaimCard(
                facts=ClaimFacts(event_type="theft", location="Berlin"),
                policy=PolicyContext(),
                citations=[
                    Citation(clause_id="A.2.2.1.2", excerpt="Theft policy wording", page=10)
                ],
                risk=RiskSignal(score=0.3, band="medium", reasons=["example reason"]),
                status=status,
            )
            conv.claim = Claim(
                status=status,
                card=card.model_dump(mode="json"),
                submitted_at=datetime(1900, 1, index + 1, tzinfo=UTC),
            )
            session.add(conv)
            session.flush()
            ids[index] = str(conv.claim.id)
        session.commit()
    with TestClient(create_app(lambda: state)) as c:
        url = "/api/claims/review-queue"
        detail = f"{url}/{ids[0]}"
        for path in (url, detail):
            assert c.get(path).status_code == 401
            assert (
                c.get(path, headers={"Authorization": "Bearer customer-token"}).status_code == 403
            )
        first = c.get(url + "?limit=1", headers=ADJUSTER).json()
        assert first["has_more"] is True
        assert first["items"][0]["id"] == ids[0]
        assert first["items"][0]["submitted_at"].startswith("1900-01-01")
        second = c.get(url + "?limit=1&offset=1", headers=ADJUSTER).json()
        assert second["items"][0]["id"] == ids[1]
        listed = c.get(url + "?limit=100", headers=ADJUSTER).json()["items"]
        assert not {ids[2], ids[3]} & {item["id"] for item in listed}
        selected = c.get(detail, headers=ADJUSTER).json()
        assert selected["card"]["facts"]["location"] == "Berlin"
        assert selected["card"]["risk"]["reasons"] == ["example reason"]
        assert selected["card"]["citations"][0]["page"] == 10
        assert (
            c.get(url + "/00000000-0000-0000-0000-000000000000", headers=ADJUSTER).status_code
            == 404
        )
        for query in ("limit=0", "limit=101", "offset=-1"):
            assert c.get(url + "?" + query, headers=ADJUSTER).status_code == 422
    # Keep repeated local runs independent without deleting unrelated test data.
    with state.session() as session:
        for claim_id in ids.values():
            claim = session.get(Claim, uuid.UUID(claim_id))
            session.delete(claim)
        session.commit()


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
        assert c.post("/api/claims/00000000-0000-0000-0000-000000000000/submit").status_code == 401
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


def test_review_needs_adjuster_role(tmp_path: Path):
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config("alembic.ini"), "head")
    policyholder = {"Authorization": "Bearer s3cret"}
    with TestClient(create_app(lambda: make_state(tmp_path / "a", token="s3cret"))) as c:
        conv = c.post("/api/conversations", json={}, headers=policyholder).json()
        url = f"/api/claims/{conv['claim_id']}/review"
        assert c.post(url, json={"decision": "accept"}, headers=policyholder).status_code == 403
        # the adjuster token also works on the policyholder routes, and passes the role check
        assert c.get(f"/api/conversations/{conv['id']}", headers=ADJUSTER).status_code == 200
        assert c.post(url, json={"decision": "accept"}, headers=ADJUSTER).status_code == 409
    with TestClient(create_app(lambda: make_state(tmp_path / "b", adjuster_token=None))) as c:
        conv = c.post("/api/conversations", json={}).json()
        r = c.post(f"/api/claims/{conv['claim_id']}/review", json={"decision": "accept"})
        assert r.status_code == 403 and "disabled" in r.json()["detail"]


def test_startup_fails_without_token_unless_open_api_allowed(tmp_path: Path):
    with pytest.raises(RuntimeError, match="DEMO_API_TOKEN"):
        with TestClient(create_app(lambda: make_state(tmp_path, allow_open_api=False))):
            pass


def test_requests_rejected_when_no_token_and_open_api_not_allowed(tmp_path: Path):
    app = create_app(lambda: make_state(tmp_path))
    with TestClient(app) as c:
        app.state.claimpilot.settings = Settings(demo_api_token=None, allow_open_api=False)
        assert c.post("/api/conversations", json={}).status_code == 503


def test_eval_page_lists_questions_with_hits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("EVAL_PAGE", "1")
    with TestClient(create_app(lambda: make_state(tmp_path))) as c:
        r = c.get("/api/eval")
        assert r.status_code == 200
        body = r.json()
        assert body["k"] == 5 and body["threshold"] == 0.8
        assert len(body["results"]) >= 25
        row = body["results"][0]
        assert {"id", "lang", "question", "expected", "retrieved", "rank", "hit"} <= set(row)
        assert set(body["summary"]) >= {"top1", "top3", "mrr"}
        assert c.get("/api/eval").json() == body  # cached per process


def test_eval_page_requires_token_and_caches_every_k(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    from api.routers import eval as eval_router

    monkeypatch.setenv("EVAL_PAGE", "1")
    eval_router._run.cache_clear()
    with TestClient(create_app(lambda: make_state(tmp_path, token="s3cret"))) as c:
        assert c.get("/api/eval").status_code == 401
        auth = {"Authorization": "Bearer s3cret"}
        for _ in range(2):
            for k in range(eval_router.K_MIN, eval_router.K_MAX + 1):
                assert c.get(f"/api/eval?k={k}", headers=auth).status_code == 200
        info = eval_router._run.cache_info()
        assert info.misses == eval_router.K_MAX - eval_router.K_MIN + 1
        assert c.get("/api/eval?k=99", headers=auth).json()["k"] == eval_router.K_MAX
        assert eval_router._run.cache_info().misses == info.misses


def test_eval_page_disabled_by_default(client: TestClient):
    assert client.get("/api/eval").status_code == 404
