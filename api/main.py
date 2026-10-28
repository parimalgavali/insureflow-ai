"""ClaimPilot API. Run: uv run uvicorn api.main:app --reload"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.config import Settings
from api.routers import claims, conversations, health
from api.routers import eval as eval_router
from api.state import AppState, build_state

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def create_app(state_factory: Callable[[], AppState] | None = None) -> FastAPI:
    factory = state_factory or build_state

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.claimpilot = factory()
        try:
            yield
        finally:
            app.state.claimpilot.close()

    app = FastAPI(title="ClaimPilot API", version="2.0.0a0", lifespan=lifespan)
    origins = list(Settings().cors_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.include_router(health.router)
    app.include_router(conversations.router)
    app.include_router(claims.router)
    app.include_router(eval_router.router)
    static_dir = os.environ.get("STATIC_DIR")
    if static_dir and os.path.isdir(static_dir):
        # single-container deployments (Hugging Face Space): serve the built Vue app from the API
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="web")
    return app


app = create_app()
