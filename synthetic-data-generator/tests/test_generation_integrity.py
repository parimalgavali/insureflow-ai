from __future__ import annotations

import json

from generator.config import GeneratorConfig
from generator.generate import generate_dataset
from generator.writer import write_dataset


def test_generated_dataset_preserves_relationships(tmp_path):
    config = GeneratorConfig(
        customers=10,
        policies=14,
        claims=8,
        adjusters=4,
        seed=11,
        output_dir=tmp_path,
    )

    dataset = generate_dataset(config)

    customer_ids = {customer.customer_id for customer in dataset.customers}
    policy_ids = {policy.policy_id for policy in dataset.policies}
    claim_ids = {claim.claim_id for claim in dataset.claims}

    assert len(dataset.customers) == 10
    assert len(dataset.policies) == 14
    assert len(dataset.claims) == 8
    assert len(dataset.adjusters) == 4

    assert all(policy.customer_id in customer_ids for policy in dataset.policies)
    assert all(coverage.policy_id in policy_ids for coverage in dataset.coverages)
    assert all(claim.policy_id in policy_ids for claim in dataset.claims)
    assert all(claim.customer_id in customer_ids for claim in dataset.claims)
    assert all(document.claim_id in claim_ids for document in dataset.claim_documents)
    assert all(event.claim_id in claim_ids for event in dataset.claim_events)
    assert all(label.claim_id in claim_ids for label in dataset.ai_triage_labels)
    assert all(payment.claim_id in claim_ids for payment in dataset.payments)


def test_generation_is_deterministic_for_same_seed(tmp_path):
    config = GeneratorConfig(
        customers=10,
        policies=14,
        claims=8,
        adjusters=4,
        seed=11,
        output_dir=tmp_path,
    )

    first_dataset = generate_dataset(config)
    second_dataset = generate_dataset(config)

    assert first_dataset == second_dataset


def test_documents_jsonl_contains_one_non_empty_document_per_synthetic_document(tmp_path):
    config = GeneratorConfig(
        customers=10,
        policies=14,
        claims=8,
        adjusters=4,
        seed=11,
        output_dir=tmp_path,
    )
    dataset = generate_dataset(config)

    write_dataset(dataset, tmp_path, seed=config.seed)

    document_lines = (tmp_path / "documents.jsonl").read_text(encoding="utf-8").splitlines()
    parsed_documents = [json.loads(line) for line in document_lines]

    assert len(parsed_documents) == len(dataset.documents)
    assert len(parsed_documents) == len(dataset.claim_documents)
    assert all(
        {"document_id", "claim_id", "document_type", "text"} <= set(document)
        for document in parsed_documents
    )
    assert all(document["text"].strip() for document in parsed_documents)
