from pathlib import Path

import pytest


@pytest.fixture
def sample_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "sample-data"
    data_dir.mkdir()
    _write_sample_csvs(data_dir)
    return data_dir


def _write_sample_csvs(data_dir: Path) -> None:
    claims = [
        (
            f"claim-{index:02d}",
            f"CLM-2026-{index:06d}",
            f"policy-{index:02d}",
            f"customer-{index % 4:02d}",
            "AUTO_COLLISION" if index % 2 == 0 else "GLASS_DAMAGE",
            "2026-01-01",
            f"2026-01-{2 + index:02d}",
            8000 + index * 3500,
            index % 3 == 0,
            index % 2 == 0,
            index % 4 != 0,
        )
        for index in range(1, 13)
    ]
    policies = [
        (
            f"policy-{index:02d}",
            f"POL-2026-{index:06d}",
            f"customer-{index % 4:02d}",
            "PERSONAL_AUTO" if index % 2 == 0 else "HOME",
            "2025-01-01",
            900 + index * 110,
            250 + (index % 3) * 250,
            25000 + (index % 4) * 25000,
        )
        for index in range(1, 13)
    ]
    labels = [
        (
            f"label-{index:02d}",
            f"claim-{index:02d}",
            ["LOW", "MEDIUM", "HIGH"][index % 3],
            ["HIGH", "LOW", "MEDIUM"][index % 3],
        )
        for index in range(1, 13)
    ]

    _write_csv(
        data_dir / "claims.csv",
        [
            "claim_id",
            "claim_number",
            "policy_id",
            "customer_id",
            "claim_type",
            "loss_date",
            "reported_date",
            "estimated_damage_eur",
            "injury_reported",
            "third_party_involved",
            "police_report_available",
        ],
        claims,
    )
    _write_csv(
        data_dir / "policies.csv",
        [
            "policy_id",
            "policy_number",
            "customer_id",
            "product_type",
            "start_date",
            "annual_premium_eur",
            "deductible_eur",
            "coverage_limit_eur",
        ],
        policies,
    )
    _write_csv(
        data_dir / "ai_triage_labels.csv",
        ["label_id", "claim_id", "severity_label", "fraud_label"],
        labels,
    )


def _write_csv(path: Path, headers: list[str], rows: list[tuple[object, ...]]) -> None:
    lines = [",".join(headers)]
    lines.extend(",".join(str(value) for value in row) for row in rows)
    path.write_text("\n".join(lines) + "\n")
