# AI Agent Guidelines

This repository (`IMODAR`) is a monorepo with a FastAPI backend (`code/backend`) and a SvelteKit frontend (`code/frontend`). It answers clinical research questions by planning SQL with a local LLM and executing it deterministically on DuckDB.

All AI agents assisting in this repository must strictly adhere to the rules below.

---

## 1. Absolute Directives & Boundaries

* **No Git Commits:** AI agents may **NEVER** run `git commit`, `git push`, or modify git history/branches unless the developer explicitly allows it in the current prompt. Permission never carries over to the next prompt. Inspecting history is allowed.
* **No Attribution:** Never add AI co-author trailers or generated-by footers to commits or pull requests.
* **No Study Data:** This repository is public. Never commit the warehouse, source files, study manifests, participant data, internal hosts, or secrets. Tests use synthetic data only.
* **File Length:** There is no hard limit, but notify the developer about files longer than 300 lines.
* **DRY & Reusability:** Never duplicate functions, models, or UI components. Extract reusable logic.

---

## 2. Documentation Pointers

* **Setup & commands:** [`README.md`](./README.md)
* **API contract:** [`code/backend/imodar/api/contracts.py`](./code/backend/imodar/api/contracts.py)
* **Design tokens:** [`code/frontend/src/app.css`](./code/frontend/src/app.css)

---

## 3. Code & Documentation Standards

* **Why, Not What:** Comments are permitted only if they explain a non-obvious rationale, workaround, or constraint. Never restate the code.
* **TODO Standards:** Leave `TODO:` comments on intentional shortcuts, stating the required future resolution.
* **Docstrings:** Document public API endpoints and exported services (Python docstrings, TSDoc). Skip trivial helpers, getters, and plain models.

---

## 4. Backend Conventions (Python / FastAPI)

* **Pipeline order:** resolve entities → plan → guard → execute → synthesise. Never bypass a stage.
* **LLM boundary:** The model plans and phrases only; it never supplies data. All model-generated SQL must pass `guard.validate` before `Warehouse.execute`.
* **Read-only warehouse:** Keep DuckDB read-only, with external access disabled and configuration locked.
* **Layers:** `imodar/api` holds HTTP concerns and depends on the pipeline. Pipeline modules never import from `imodar/api`.
* **Contracts:** Use `…Request`/`…Response` for top-level bodies and plain nouns for nested types. Type closed value sets as `Literal` or enums.
* **Errors:** Never return internal hosts, paths, or stack traces to clients.
* **Testing:** Pytest is required for new logic. Stub Ollama and Qdrant; never require the real warehouse.

---

## 5. Frontend Conventions (SvelteKit / Svelte 5)

* **Reactivity:** Use runes (`$state`, `$derived`, `$props`, `$effect`) exclusively. Prefer `$derived` over `$effect`.
* **Components:** Check `src/lib/components` before creating one. Keep them small and focused.
* **Styling:** Use scoped CSS and the tokens in `app.css`. Follow the Figma design.
* **Rendering untrusted text:** Never use `{@html}` for model or API output.
* **Pessimistic UI:** Update state only after a successful response. Show loading and disabled states.
* **Generated API types:** Contract types come **only** from `src/lib/api/schema.ts`. Never edit it or `code/backend/openapi/imodar.json` by hand; regenerate them.
* **Testing:** Unit tests are Vitest `*.spec.ts`. User flows are Playwright `e2e/*.e2e.ts`. Never test user flows in Vitest.
* **Accessibility:** Target WCAG AA: labelled controls, keyboard access, visible focus.
* **Placeholders:** Unconnected features must be disabled and visibly marked, never faked.

---

## 6. Quality Guard

Run the checks in [`README.md`](./README.md) for every area you changed. CI also runs Gitleaks, Semgrep, and Trivy.
