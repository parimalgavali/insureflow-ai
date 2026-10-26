from __future__ import annotations

import csv
import json

from generator.config import GeneratorConfig
from generator.generate import generate_dataset
from generator.writer import write_dataset


def test_writer_outputs_stable_csv_headers_and_summary_counts(tmp_path):
    config = GeneratorConfig(customers=5, policies=6, claims=4, adjusters=3, seed=7)
    dataset = generate_dataset(config)

    write_dataset(dataset, tmp_path, seed=config.seed)

    with (tmp_path / "customers.csv").open(encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file)
        assert next(reader) == [
            "customer_id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "city",
            "country",
            "date_of_birth",
            "created_at",
        ]

    with (tmp_path / "claims.csv").open(encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file)
        assert next(reader) == [
            "claim_id",
            "claim_number",
            "policy_id",
            "customer_id",
            "adjuster_id",
            "claim_type",
            "status",
            "loss_date",
            "reported_date",
            "loss_city",
            "description",
            "estimated_damage_eur",
            "injury_reported",
            "third_party_involved",
            "police_report_available",
        ]

    summary = json.loads((tmp_path / "generation_summary.json").read_text(encoding="utf-8"))
    assert summary == {
        "customers": len(dataset.customers),
        "policies": len(dataset.policies),
        "coverages": len(dataset.coverages),
        "claims": len(dataset.claims),
        "claim_documents": len(dataset.claim_documents),
        "claim_notes": len(dataset.claim_notes),
        "claim_events": len(dataset.claim_events),
        "adjusters": len(dataset.adjusters),
        "payments": len(dataset.payments),
        "ai_triage_labels": len(dataset.ai_triage_labels),
        "documents": len(dataset.documents),
        "seed": config.seed,
    }


def test_writer_outputs_valid_jsonl_documents(tmp_path):
    config = GeneratorConfig(customers=5, policies=6, claims=4, adjusters=3, seed=7)
    dataset = generate_dataset(config)

    write_dataset(dataset, tmp_path, seed=config.seed)

    lines = (tmp_path / "documents.jsonl").read_text(encoding="utf-8").splitlines()
    assert lines
    assert all(json.loads(line) for line in lines)
