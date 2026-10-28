from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine

DEFAULT_DATABASE_URL = "postgresql+psycopg://claimpilot:claimpilot@localhost:5432/claimpilot"


def database_url() -> str:
    """DATABASE_URL, normalised to the psycopg3 driver (hosted Postgres hands out `postgresql://`)."""
    url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    elif url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://") :]
    return url


def get_engine(url: str | None = None) -> Engine:
    return create_engine(url or database_url(), pool_pre_ping=True)
