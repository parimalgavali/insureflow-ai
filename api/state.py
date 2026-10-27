"""Everything the request handlers share: DB engine, agent graph, retriever, provider."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker

from api.agent.graph import AgentDeps, RetrieverLike, RiskScorer, build_graph
from api.config import Settings
from api.llm.provider import Provider, RecordedProvider, make_provider
from db.session import get_engine

log = logging.getLogger("claimpilot")


@dataclass
class AppState:
    settings: Settings
    engine: Engine
    graph: Any
    provider: Provider
    retriever: RetrieverLike | None = None
    risk_scorer: RiskScorer | None = None
    close: Callable[[], None] = field(default=lambda: None)

    def session(self) -> Session:
        return sessionmaker(bind=self.engine, expire_on_commit=False)()

    def health(self) -> dict[str, Any]:
        report: dict[str, Any] = {
            "provider": self.provider.name,
            "retriever": self.retriever is not None,
        }
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                chunks = conn.execute(text("SELECT count(*) FROM policy_chunks")).scalar_one()
            report["db"] = "ok"
            report["policy_chunks"] = int(chunks)
        except Exception as exc:  # noqa: BLE001
            report["db"] = f"error: {exc.__class__.__name__}"
        report["risk_model"] = (
            getattr(self.risk_scorer, "model_version", None) if self.risk_scorer else None
        )
        report["status"] = "ok" if report.get("db") == "ok" else "degraded"
        return report


def build_provider(settings: Settings) -> Provider:
    if settings.llm_provider == "recorded":
        return RecordedProvider(settings.recorded_fixture)
    return make_provider(settings.llm_provider)


def build_retriever(engine: Engine, settings: Settings) -> RetrieverLike | None:
    try:
        from rag.embeddings import Embedder
        from rag.query_rewrite import AnthropicRewriter, NoRewriter, RecordedRewriter
        from rag.retriever import Retriever
        from rag.store import PgVectorStore

        store = PgVectorStore(engine=engine)
        if store.count() == 0:
            log.warning("policy_chunks is empty; run `python -m rag.ingest` — retrieval disabled")
            return None
        if settings.llm_provider == "anthropic":
            rewriter = AnthropicRewriter()
        elif settings.llm_provider == "recorded":
            rewriter = RecordedRewriter()
        else:
            rewriter = NoRewriter()
        return Retriever(store, Embedder(), rewriter)
    except Exception as exc:  # noqa: BLE001
        log.warning("retrieval disabled: %s", exc)
        return None


def build_risk_scorer() -> RiskScorer | None:
    try:
        from ml.predict import load_scorer  # provided by task 2

        return load_scorer()
    except Exception as exc:  # noqa: BLE001
        log.warning("risk model unavailable: %s", exc)
        return None


def build_checkpointer(settings: Settings):
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool

    pool = ConnectionPool(
        settings.psycopg_dsn,
        min_size=1,
        max_size=5,
        kwargs={"autocommit": True, "row_factory": dict_row},
    )
    return PostgresSaver(pool), pool.close


def build_state(settings: Settings | None = None) -> AppState:
    settings = settings or Settings()
    engine = get_engine(settings.database_url)
    provider = build_provider(settings)
    retriever = build_retriever(engine, settings)
    scorer = build_risk_scorer()
    checkpointer, close = build_checkpointer(settings)
    graph = build_graph(
        AgentDeps(provider=provider, retriever=retriever, risk_scorer=scorer), checkpointer
    )
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return AppState(settings, engine, graph, provider, retriever, scorer, close)
