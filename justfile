mod api 'just/api.just'
mod web 'just/web.just'

# List available recipes
[private]
default:
    @just --list --list-submodules

# Start databases, migrate, and run the API and frontend with hot reload
dev: up
    #!/usr/bin/env bash
    set -euo pipefail
    just api migrate
    trap 'kill $(jobs -p) 2>/dev/null || true' EXIT
    just api dev &
    just web dev &
    wait -n

# Start Postgres and Qdrant
up:
    docker compose up -d --wait

# Stop Postgres and Qdrant (data is kept)
down:
    docker compose down

# Install all dependencies
install:
    just api install
    just web install

# Format all code
fmt:
    just api fmt
    just web fmt

# Check formatting for all code
fmt-check:
    just api fmt-check
    just web fmt-check

# Lint all code
lint:
    just api lint
    just web lint

# Type-check the frontend
typecheck:
    just web typecheck

# Run all test suites
test:
    just api test
    just web test

# Build the frontend for production
build:
    just web build

# Audit dependencies for vulnerabilities
audit:
    just web audit

# Regenerate the OpenAPI spec and the frontend API types after a contract change
gen-api:
    just api openapi
    just web gen-api

# Run every check that CI runs
check: fmt-check lint typecheck test build

# Clean build artifacts, caches, and test results
clean:
    just api clean
    just web clean
