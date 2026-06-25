from __future__ import annotations

import argparse
from pathlib import Path

from insureflow_ml.features import load_training_frame
from insureflow_ml.training import train_all


def main() -> None:
    parser = argparse.ArgumentParser(description="Train InsureFlow AI triage ML models.")
    parser.add_argument("--data-dir", type=Path, default=Path("../data/synthetic"))
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    frame = load_training_frame(args.data_dir)
    results = train_all(frame, args.artifacts_dir, random_state=args.random_state)
    for result in results:
        print(
            f"{result.target}: macroF1={result.macro_f1:.4f} "
            f"balancedAccuracy={result.balanced_accuracy:.4f} "
            f"artifactDir={result.artifact_dir}"
        )


if __name__ == "__main__":
    main()
