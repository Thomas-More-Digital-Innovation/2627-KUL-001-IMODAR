# IMODAR

Ask clinical questions across heterogeneous studies. A local LLM plans SQL, an AST guardrail validates it, and DuckDB executes it read-only. Every answer includes an audit trail.

> **Not ready for deployment.** Every signed-in user can query every study, and user management is still a preview with sample data.

## Structure

- `code/backend`: FastAPI and the query pipeline (Python, uv)
- `code/frontend`: SvelteKit application (Node 24, npm)
- `k8s`: Argo CD deployment, see [`k8s/README.md`](./k8s/README.md)

## Run

Requires [just](https://just.systems), uv, Node 24, Docker, Ollama (with the planner and `bge-m3` models), and a warehouse built by the PoC ingest, which is not in this repository.

```bash
just install
cp code/backend/.env.example code/backend/.env   # fill it in; `just api secret-key` prints a key
just up
just api migrate
just api seed-admin
just dev
```

Open the URL Vite prints (normally <http://localhost:5173>). The first sign-in sets up two-factor authentication, which is mandatory. Seeding never changes an existing account; remove `ADMIN_PASSWORD` from `.env` afterwards.

The frontend proxies `/api` to `BACKEND_URL` (default `http://127.0.0.1:8000`). Application data lives in Postgres, separate from the study warehouse. Other settings are in `code/backend/imodar/config.py`.

## Commands

Run `just` to list everything.

```bash
just check                              # everything CI checks
just test                               # all tests (needs Docker)
just web playwright-install             # once, before the e2e tests
just fmt
just gen-api                            # after an API contract change
just api migration "describe change"    # after a model change
```
