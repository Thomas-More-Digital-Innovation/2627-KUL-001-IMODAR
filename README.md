# IMODAR

Ask clinical questions across heterogeneous studies. A local LLM plans SQL, an AST guardrail validates it, and DuckDB executes it read-only. Every answer includes an audit trail.

> **Not ready for deployment.** There is no authentication yet; keep both servers on localhost. Login, settings and admin screens are previews with sample data.

## Structure

- `code/backend`: FastAPI and the query pipeline (Python, uv)
- `code/frontend`: SvelteKit application (Node 24, npm)

## Run

Requires Ollama (with the planner and `bge-m3` models) and a warehouse built by the PoC ingest, which is not in this repository.

```bash
docker compose up -d

cd code/backend
IMODAR_WAREHOUSE=/path/to/warehouse OLLAMA_URL=http://localhost:11434 \
  uv run uvicorn imodar.api.main:app --reload

cd code/frontend
npm ci
npm run dev
```

The frontend proxies `/api` to `BACKEND_URL` (default `http://127.0.0.1:8000`). Other settings are in `code/backend/imodar/config.py`.

## Checks

```bash
cd code/backend
uv run ruff check . && uv run ruff format --check . && uv run pytest

cd code/frontend
npm run lint && npm run format:check && npm run check
npm run test:unit
npx playwright install chromium && npm run test:e2e
```

After changing the API contract:

```bash
(cd code/backend && uv run python scripts/export_openapi.py)
(cd code/frontend && npm run gen:api)
```
