set working-directory := '../code/frontend'

# Clean install frontend dependencies
install:
    npm ci

# Run the frontend with hot reload
dev:
    npm run dev

# Format frontend code
fmt:
    npm run format

# Check frontend formatting
fmt-check:
    npm run format:check

# Lint frontend code
lint:
    npm run lint

# Run Svelte and TypeScript checks
typecheck:
    npm run check

# Run all tests (unit + e2e)
test: test-unit test-e2e

# Run unit tests only
test-unit:
    npm run test:unit

# Run e2e tests only
test-e2e *args:
    npm run test:e2e -- {{args}}

# Install Playwright's browser and system dependencies
playwright-install:
    npx playwright install --with-deps chromium

# Build for production
build:
    npm run build

# Regenerate API types from the OpenAPI spec
gen-api:
    npm run gen:api

# Audit npm dependencies
audit:
    npm audit

# Clean build artifacts and test reports
clean:
    rm -rf build .svelte-kit test-results playwright-report
