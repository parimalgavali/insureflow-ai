from rag_service.audit import InMemoryRagAuditStore
from rag_service.schemas import IngestRequest, QueryRequest
from rag_service.service import RagAssistantService


def test_query_limits_sources_to_top_k_and_audits_retrieved_chunks():
    audit_store = InMemoryRagAuditStore()
    service = RagAssistantService(audit_store=audit_store)
    service.ingest(
        IngestRequest(
            document_id="DOC-GUIDE-001",
            claim_id="CLM-ID-001",
            policy_id=None,
            document_type="CLAIMS_GUIDELINE",
            title="Motor Claim Guide",
            text=(
                "Collision Coverage\n"
                "Collision claims should verify active policy status and damage photos.\n\n"
                "Police Report\n"
                "Third-party collision claims should request a police report.\n\n"
                "Medical Review\n"
                "Injury claims should request medical notes."
            ),
        )
    )

    response = service.query(
        QueryRequest(claim_id="CLM-ID-001", question="What documents are missing for third-party collision?", top_k=1)
    )

    assert len(response.sources) == 1
    assert response.sources[0].chunk_id == "DOC-GUIDE-001-CHUNK-0002"
    audit_record = audit_store.get(response.audit_id)
    assert audit_record is not None
    assert audit_record.question == "What documents are missing for third-party collision?"
    assert audit_record.retrieved_chunk_ids == ["DOC-GUIDE-001-CHUNK-0002"]
    assert audit_record.prompt_version == "v1"


def test_unrelated_question_returns_no_sources():
    service = RagAssistantService()
    service.ingest(
        IngestRequest(
            document_id="DOC-POLICY-002",
            claim_id="CLM-ID-002",
            policy_id="POL-ID-002",
            document_type="POLICY_DOCUMENT",
            title="Motor Policy",
            text="Collision Coverage\nCollision damage is covered when the policy is active.",
        )
    )

    response = service.query(QueryRequest(claim_id="CLM-ID-002", question="How do I change my email address?", top_k=3))

    assert response.sources == []
    assert response.confidence == "LOW"
    assert "do not have enough retrieved evidence" in response.answer
