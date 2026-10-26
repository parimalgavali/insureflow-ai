from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from generator.models import GeneratedDataset

OUTPUT_FILES = [
    "customers.csv",
    "policies.csv",
    "coverages.csv",
    "claims.csv",
    "claim_documents.csv",
    "claim_notes.csv",
    "claim_events.csv",
    "adjusters.csv",
    "payments.csv",
    "ai_triage_labels.csv",
    "documents.jsonl",
    "generation_summary.json",
]


def _write_csv(path: Path, rows: Iterable[object], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _write_jsonl(path: Path, rows: Iterable[object]) -> None:
    with path.open("w", encoding="utf-8") as jsonl_file:
        for row in rows:
            jsonl_file.write(json.dumps(asdict(row), sort_keys=True) + "\n")


def write_dataset(dataset: GeneratedDataset, output_dir: Path, *, seed: int) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_specs = {
        "customers.csv": (
            dataset.customers,
            [
                "customer_id",
                "first_name",
                "last_name",
                "email",
                "phone",
                "city",
                "country",
                "date_of_birth",
                "created_at",
            ],
        ),
        "policies.csv": (
            dataset.policies,
            [
                "policy_id",
                "policy_number",
                "customer_id",
                "product_type",
                "status",
                "start_date",
                "end_date",
                "annual_premium_eur",
                "deductible_eur",
                "coverage_limit_eur",
            ],
        ),
        "coverages.csv": (
            dataset.coverages,
            ["coverage_id", "policy_id", "coverage_type", "limit_eur", "deductible_eur", "active"],
        ),
        "claims.csv": (
            dataset.claims,
            [
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
            ],
        ),
        "claim_documents.csv": (
            dataset.claim_documents,
            ["document_id", "claim_id", "document_type", "received_at", "source"],
        ),
        "claim_notes.csv": (
            dataset.claim_notes,
            ["note_id", "claim_id", "adjuster_id", "created_at", "note_type", "body"],
        ),
        "claim_events.csv": (
            dataset.claim_events,
            ["event_id", "claim_id", "event_type", "occurred_at", "actor", "description"],
        ),
        "adjusters.csv": (
            dataset.adjusters,
            [
                "adjuster_id",
                "employee_number",
                "first_name",
                "last_name",
                "region",
                "authority_limit_eur",
                "active",
            ],
        ),
        "payments.csv": (
            dataset.payments,
            ["payment_id", "claim_id", "amount_eur", "payment_date", "payment_type", "status"],
        ),
        "ai_triage_labels.csv": (
            dataset.ai_triage_labels,
            [
                "label_id",
                "claim_id",
                "severity_score",
                "severity_label",
                "fraud_score",
                "fraud_label",
                "litigation_score",
                "litigation_label",
                "reason_codes",
                "model_version",
            ],
        ),
    }

    for file_name, (rows, fieldnames) in csv_specs.items():
        _write_csv(output_dir / file_name, rows, fieldnames)

    _write_jsonl(output_dir / "documents.jsonl", dataset.documents)

    summary = {
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
        "seed": seed,
    }
    (output_dir / "generation_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary
