from fastapi.testclient import TestClient

from rag_service.app import app


def test_health_endpoint():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "rag-service"}


def test_ingest_query_and_list_chunks():
    client = TestClient(app)

    ingest_response = client.post(
        "/ai/v1/rag/ingest",
        json={
            "documentId": "DOC-POLICY-001",
            "claimId": "CLM-ID-001",
            "policyId": "POL-ID-001",
            "documentType": "POLICY_DOCUMENT",
            "title": "Motor Policy Coverage",
            "text": (
                "Collision Coverage\n"
                "Collision damage is covered when the policy is active on the loss date.\n\n"
                "Exclusions\n"
                "Wear and tear is excluded from collision coverage."
            ),
            "metadata": {"sourceSystem": "synthetic-demo"},
        },
    )

    assert ingest_response.status_code == 200
    assert ingest_response.json() == {
        "documentId": "DOC-POLICY-001",
        "chunkCount": 2,
        "chunkIds": ["DOC-POLICY-001-CHUNK-0001", "DOC-POLICY-001-CHUNK-0002"],
    }

    chunks_response = client.get("/ai/v1/rag/documents/DOC-POLICY-001/chunks")
    assert chunks_response.status_code == 200
    chunks = chunks_response.json()["chunks"]
    assert [chunk["chunkId"] for chunk in chunks] == [
        "DOC-POLICY-001-CHUNK-0001",
        "DOC-POLICY-001-CHUNK-0002",
    ]
    assert chunks[0]["sectionTitle"] == "Collision Coverage"

    query_response = client.post(
        "/ai/v1/rag/query",
        json={"claimId": "CLM-ID-001", "question": "Is this collision loss covered?", "topK": 2},
    )

    assert query_response.status_code == 200
    body = query_response.json()
    assert "collision damage appears potentially covered" in body["answer"]
    assert body["confidence"] == "MEDIUM"
    assert body["requiresHumanReview"] is True
    assert body["promptName"] == "rag_adjuster_assistant"
    assert body["promptVersion"] == "v1"
    assert body["auditId"]
    assert body["sources"][0]["documentId"] == "DOC-POLICY-001"
    assert body["sources"][0]["chunkId"] == "DOC-POLICY-001-CHUNK-0001"


def test_query_without_evidence_returns_missing_evidence_answer():
    client = TestClient(app)

    response = client.post(
        "/ai/v1/rag/query",
        json={"claimId": "CLM-ID-404", "question": "Which exclusion applies to flood damage?", "topK": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["sources"] == []
    assert body["confidence"] == "LOW"
    assert body["requiresHumanReview"] is True
    assert "do not have enough retrieved evidence" in body["answer"]
