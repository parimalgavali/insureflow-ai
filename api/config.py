"""Runtime settings, all from environment variables (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from db.session import database_url


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=database_url)
    llm_provider: str = field(default_factory=lambda: os.environ.get("LLM_PROVIDER", "anthropic"))
    demo_api_token: str | None = field(
        default_factory=lambda: os.environ.get("DEMO_API_TOKEN") or None
    )
    upload_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("UPLOAD_DIR", "data/uploads"))
    )
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            o.strip()
            for o in os.environ.get(
                "CORS_ORIGINS", "http://localhost:5173,http://localhost:8080"
            ).split(",")
            if o.strip()
        )
    )
    max_upload_bytes: int = field(
        default_factory=lambda: int(os.environ.get("MAX_UPLOAD_MB", "10")) * 1024 * 1024
    )
    recorded_fixture: Path = field(
        default_factory=lambda: Path(
            os.environ.get("RECORDED_FIXTURE", "tests/fixtures/agent/hit_and_run.json")
        )
    )

    @property
    def psycopg_dsn(self) -> str:
        return self.database_url.replace("postgresql+psycopg://", "postgresql://", 1)
