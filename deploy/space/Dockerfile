# ClaimPilot on a Hugging Face Space (Docker SDK): API + built frontend in one container, port 7860.
# Database: external Postgres with pgvector (DATABASE_URL secret, e.g. Neon). LLM: ANTHROPIC_API_KEY secret.
FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy HF_HOME=/models HF_HUB_DISABLE_TELEMETRY=1
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/
RUN useradd -m -u 1000 user && mkdir -p /app /models && chown -R user:user /app /models
WORKDIR /app
COPY --chown=user pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --extra data --extra rag --extra llm --extra agent --extra api --extra ml
ENV PATH="/app/.venv/bin:$PATH"
# bake the embedding model into the image so cold starts don't download 470 MB
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-small')" && chown -R user:user /models
COPY --chown=user api ./api
COPY --chown=user rag ./rag
COPY --chown=user ml ./ml
COPY --chown=user db ./db
COPY --chown=user scripts ./scripts
COPY --chown=user alembic.ini ./
COPY --chown=user data/README.md ./data/README.md
COPY --chown=user --from=web /web/dist ./static
COPY --chown=user deploy/space/entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh
USER user
ENV STATIC_DIR=/app/static UPLOAD_DIR=/app/data/uploads PORT=7860 EVAL_PAGE=1
EXPOSE 7860
CMD ["./entrypoint.sh"]
