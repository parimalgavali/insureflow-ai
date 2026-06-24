from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GeneratorConfig:
    customers: int = 500
    policies: int = 650
    claims: int = 200
    adjusters: int = 25
    seed: int = 42
    output_dir: Path = Path("data/synthetic")
