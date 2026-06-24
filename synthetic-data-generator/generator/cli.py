from __future__ import annotations

import argparse
from pathlib import Path

from generator.config import GeneratorConfig
from generator.generate import generate_dataset
from generator.writer import write_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic InsureFlow AI demo data.")
    parser.add_argument("--customers", type=int, default=500)
    parser.add_argument("--policies", type=int, default=650)
    parser.add_argument("--claims", type=int, default=200)
    parser.add_argument("--adjusters", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=Path("data/synthetic"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = GeneratorConfig(
        customers=args.customers,
        policies=args.policies,
        claims=args.claims,
        adjusters=args.adjusters,
        seed=args.seed,
        output_dir=args.output_dir,
    )
    dataset = generate_dataset(config)
    write_dataset(dataset, config.output_dir, seed=config.seed)
    return 0
