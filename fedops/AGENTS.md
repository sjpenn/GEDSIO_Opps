# Repository Guidelines

## Project Structure & Module Organization
- Backend lives under `fedops_api/` (FastAPI entry `main.py` and routers) and `fedops_core/` (settings, DB engine, schemas, services, pipelines). Data sources and matching live in `fedops_sources/`, while agent orchestration is in `fedops_agents/`. 
- Frontend lives in `frontend/` (Vite + React + Tailwind) with feature pages in `src/pages`, shared UI in `src/components`, utilities in `src/lib` and `src/services`, and tests in `src/App.test.tsx` + `src/setupTests.ts`.
- Migrations are managed in `alembic/` with config in `alembic.ini`. Sample/local artifacts sit in `data/`, `uploads/`, and `static/`; avoid committing generated files there unless intentional.
- Python tests sit in `tests/` alongside a few top-level `test_*.py` helpers; scripts and one-off tools are in `scripts/` and root-level `check_*.py`.

## Build, Test, and Development Commands
- Full stack: `docker compose up --build` from repo root (relies on `.env`; copy `.env.example` if missing).
- Backend only: `uvicorn fedops_api.main:app --reload` (ensure Postgres URL and API keys are in `.env`).
- Backend tests: `pytest tests` (adds async/http coverage); target a failing-first test before coding.
- Frontend: `cd frontend && npm install` once, then `npm run dev` for local, `npm run build` for production bundle, `npm run lint` for ESLint, and `npm run test` for Vitest/RTL.

## Coding Style & Naming Conventions
- Python: follow PEP8 with 4-space indents and type hints; async services should expose clear verb-based coroutine names. Pydantic schemas live in `fedops_core/schemas`; keep request/response models suffixed with `Create/Update/Response`. Prefer SQLAlchemy models in `fedops_core/db` and migrations via Alembic over ad-hoc DDL.
- TypeScript: use strict typing, PascalCase for components, camelCase for hooks/utilities, and colocate styles via Tailwind classes. Keep API clients in `src/services` and shared types in `src/types.ts`. ESLint runs automatically via `npm run lint`; align with its autofix output.

## Testing Guidelines
- Python tests use `pytest` + `TestClient` fixtures (`tests/conftest.py`); name files `test_*.py` and target business logic or routers with small fixtures instead of external services. Mock outbound model calls and persist deterministic sample payloads in `data/`.
- Frontend tests use Vitest + React Testing Library; prefer user-facing assertions and keep component tests near the component or under `src/__tests__/` if they grow.

## Commit & Pull Request Guidelines
- Commits follow Conventional Commits (e.g., `feat: ...`, `fix: ...`, `chore: ...`) as seen in git history; keep messages present-tense and scoped.
- Pull requests should include a concise summary, linked issue/story ID, evidence of tests run (`pytest`, `npm run test`, `npm run lint`), and screenshots or GIFs for UI-facing changes. Note any schema or migration impacts and add rollout notes when touching data pipelines or agents.

## Database Migration Workflow
- Create migrations with Alembic from repo root: `alembic revision --autogenerate -m "describe change"`; review generated files in `alembic/versions/` for indexes, FKs, and defaults before committing.
- Apply locally with `alembic upgrade head` (ensure DB URL in `.env`). Keep SQLAlchemy models in `fedops_core/db` aligned with migrations to avoid drift.
- For seed/backfill steps, prefer explicit scripts in `scripts/` and call them in release notes; avoid irreversible data mutations inside migrations when possible.

## CI & Verification Pointers
- Before pushing, run `pytest tests`, `npm run lint`, and `npm run test` (frontend) to mirror expected CI checks. If working inside containers, `docker compose run --rm api pytest` or equivalent is acceptable.
- Smoke check after backend changes: `curl http://localhost:8000/health`. For UI work, validate primary flows in `frontend/src/pages` you touched and capture screenshots for the PR.
