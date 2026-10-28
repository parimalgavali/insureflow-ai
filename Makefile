.PHONY: demo dev test e2e lint down

demo:            ## fetch data, train/ingest, docker compose up (http://localhost:8080)
	./scripts/demo.sh

dev:             ## API + Vite dev server against local Postgres (recorded LLM)
	uv run alembic upgrade head
	(LLM_PROVIDER=$${LLM_PROVIDER:-recorded} uv run uvicorn api.main:app --reload &) && cd web && npm run dev

test:            ## python + web unit tests
	uv run pytest -q
	cd web && npm test

e2e:             ## Playwright smoke test (starts API + Vite itself)
	cd web && npm run e2e

lint:
	uv run ruff check . && uv run ruff format --check .
	cd web && npm run typecheck

down:
	docker compose down
