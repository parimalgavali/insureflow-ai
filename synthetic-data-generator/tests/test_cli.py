from __future__ import annotations

import subprocess
import sys


EXPECTED_OUTPUT_FILES = [
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


def test_cli_generates_expected_output_files(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "generator",
            "--customers",
            "5",
            "--policies",
            "6",
            "--claims",
            "4",
            "--adjusters",
            "3",
            "--seed",
            "7",
            "--output-dir",
            str(tmp_path),
        ],
        check=False,
        cwd=".",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(EXPECTED_OUTPUT_FILES)
