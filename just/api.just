set working-directory := '../code/backend'

test_db := env('TEST_DATABASE_URL', 'postgresql+psycopg://imodar:imodar@localhost:5432/imodar_test')

# Install backend dependencies
install:
    uv sync --locked

# Run the API with hot reload
dev:
    uv run uvicorn imodar.api.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir imodar

# Format Python code
fmt:
    uv run ruff format .

# Check Python formatting
fmt-check:
    uv run ruff format --check .

# Lint Python code
lint:
    uv run ruff check .

# Auto-fix lint findings
lint-fix:
    uv run ruff check --fix .

# Run unit tests only (database tests are skipped)
test-unit *args:
    env -u TEST_DATABASE_URL uv run pytest {{args}}

# Run all tests against the test database
test *args: create-test-db
    TEST_DATABASE_URL='{{test_db}}' uv run pytest {{args}}

# Create the local test database if needed
create-test-db:
    #!/usr/bin/env bash
    set -euo pipefail
    [ -z "${TEST_DATABASE_URL:-}" ] || exit 0
    docker compose up -d --wait postgres
    docker compose exec -T postgres psql -U imodar -tAc "SELECT 1 FROM pg_database WHERE datname = 'imodar_test'" | grep -q 1 \
      || docker compose exec -T postgres createdb -U imodar imodar_test

# Apply database migrations
migrate:
    uv run alembic upgrade head

# Generate a migration from model changes
migration message:
    uv run alembic revision --autogenerate -m "{{message}}"

# Create the first admin from .env
seed-admin:
    uv run python -m imodar.auth.seed_admin

# Print a new APP_SECRET_KEY
secret-key:
    @uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Export the OpenAPI spec
openapi:
    uv run python scripts/export_openapi.py

# Clean caches
clean:
    rm -rf .pytest_cache .ruff_cache
    find . -name __pycache__ -type d -not -path './.venv/*' -prune -exec rm -rf {} +
