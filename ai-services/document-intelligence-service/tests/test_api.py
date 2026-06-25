from fastapi.testclient import TestClient

from document_intelligence.app import app


def test_health_endpoints():
    client = TestClient(app)

    root_response = client.get("/health")
    document_response = client.get("/ai/v1/documents/health")

    assert root_response.status_code == 200
    assert root_response.json() == {"status": "ok", "service": "document-intelligence-service"}
    assert document_response.status_code == 200
    assert document_response.json() == {"status": "ok", "service": "document-intelligence-service"}


def test_extract_claim_description_returns_structured_fields():
    client = TestClient(app)

    response = client.post(
        "/ai/v1/documents/extract",
        json={
            "claimId": "CLM-ID-001",
            "claimNumber": "CLM-20260626-000001",
            "documentId": "DOC-001",
            "documentType": "CLAIM_DESCRIPTION",
            "text": (
                "I was driving near Bielefeld when another car hit my rear bumper. "
                "The driver left the scene. I have photos but no police report yet. "
                "Damage is around 4500 EUR."
            ),
            "knownDocuments": ["DAMAGE_PHOTOS"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["promptName"] == "claim_description_extraction"
    assert body["promptVersion"] == "v1"
    assert body["modelName"] == "deterministic-document-intelligence"
    assert body["auditId"]
    assert body["extractedFields"] == {
        "claimType": "MOTOR_COLLISION",
        "damageType": "REAR_BUMPER",
        "thirdPartyInvolved": True,
        "policeReportAvailable": False,
        "possibleHitAndRun": True,
        "estimatedDamageAmount": 4500,
        "injuryReported": False,
        "requiredDocuments": ["POLICE_REPORT", "DAMAGE_PHOTOS", "REPAIR_ESTIMATE"],
    }
    assert body["validationWarnings"] == []


def test_extract_repair_invoice_returns_invoice_fields():
    client = TestClient(app)

    response = client.post(
        "/ai/v1/documents/extract",
        json={
            "claimId": "CLM-ID-002",
            "claimNumber": "CLM-20260626-000002",
            "documentId": "DOC-002",
            "documentType": "REPAIR_INVOICE",
            "text": (
                "Invoice INV-2026-10042 from Example Auto Repair GmbH. "
                "Labor cost 1200 EUR. Parts cost 2800 EUR. Tax 760 EUR. Total 4760 EUR."
            ),
        },
    )

    assert response.status_code == 200
    assert response.json()["extractedFields"] == {
        "invoiceNumber": "INV-2026-10042",
        "repairShop": "Example Auto Repair GmbH",
        "laborCost": 1200,
        "partsCost": 2800,
        "taxAmount": 760,
        "totalAmount": 4760,
        "currency": "EUR",
    }


def test_missing_check_flags_required_motor_documents():
    client = TestClient(app)

    response = client.post(
        "/ai/v1/documents/missing-check",
        json={
            "claimId": "CLM-ID-001",
            "claimNumber": "CLM-20260626-000001",
            "claimType": "MOTOR_COLLISION",
            "injuryReported": False,
            "thirdPartyInvolved": True,
            "policeReportAvailable": False,
            "knownDocuments": ["DAMAGE_PHOTOS"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["promptName"] == "missing_documents"
    assert body["promptVersion"] == "v1"
    assert body["missingDocuments"] == ["POLICE_REPORT", "REPAIR_ESTIMATE"]
    assert body["requiresHumanReview"] is True
    assert "Police report" in body["explanation"]


def test_summarize_returns_required_adjuster_sections():
    client = TestClient(app)

    response = client.post(
        "/ai/v1/documents/summarize",
        json={
            "claimId": "CLM-ID-001",
            "claimNumber": "CLM-20260626-000001",
            "claimType": "MOTOR_COLLISION",
            "policyStatus": "ACTIVE",
            "coverageStatus": "COVERED",
            "incidentDetails": "Rear bumper collision near Bielefeld.",
            "documentsReceived": ["DAMAGE_PHOTOS", "REPAIR_INVOICE"],
            "missingDocuments": ["POLICE_REPORT"],
            "triage": {"severity": "HIGH", "fraud": "MEDIUM", "litigation": "LOW"},
            "keyInconsistencies": ["Invoice amount exceeds initial estimate."],
            "recommendedNextAction": "Request police report and assign to senior motor adjuster.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body["sections"].keys()) == {
        "claimOverview",
        "policyAndCoverageStatus",
        "incidentDetails",
        "documentsReceived",
        "missingDocuments",
        "aiRiskScores",
        "keyInconsistencies",
        "recommendedNextAction",
        "humanReviewWarning",
    }
    assert "decision support only" in body["sections"]["humanReviewWarning"]
    assert "Claim CLM-20260626-000001" in body["summaryText"]
