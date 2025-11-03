# Day 1 — Project analysis & quick triage

Date: 2025-11-03
Branch: feat/day1-analysis (recommended; not created by this run)

## What I ran (commands executed)
- `PYTHONPATH=. pytest -q` (tests run)
- `PYTHONPATH=. pytest --cov=app --cov-report=term-missing` (coverage summary)
- `PYTHONPATH=. pytest --cov=app --cov-report=xml:reports/coverage.xml --cov-report=html:reports/htmlcov` (coverage artifacts)
- `ruff check .` (lint)
- `mypy --ignore-missing-imports .` (type checks)

All raw outputs saved under `reports/`:
- `reports/pytest-output.txt`
- `reports/pytest-coverage-term.txt`
- `reports/coverage.xml`
- `reports/htmlcov/` (coverage HTML)
- `reports/lint-ruff.txt`
- `reports/mypy.txt`

## Test & coverage baseline
- Tests: 5 passed, 0 failed (2 warnings). (See `reports/pytest-output.txt`)
- Coverage: TOTAL 74% (details below)

Coverage by file (important highlights):
- `app/routers/exercises.py` — 43% (lots of missed branches/lines)
- `app/routers/sessions.py` — 43% (lots of missed branches/lines)
- `app/main.py`, `app/models.py`, `app/database.py`, `app/schemas.py` — 100% reported

Overall: 74% (above the 70% target for the assignment baseline, but router modules are under-tested).

## Linter & type-check summary
- `ruff` found multiple issues (see `reports/lint-ruff.txt`). Representative items:
  - Duplicate / incorrectly-placed imports in `app/main.py` and `app/schemas.py` (E402/F811)
  - Multiple statements on one line in `app/routers/exercises.py` (E701)
  - Unused imports in tests (F401)
  - Several fixable issues (ruff reported 13 fixable items)
- `mypy` found type problems primarily in `app/schemas.py` and `app/routers/*.py` where SQLAlchemy Column objects were passed to Pydantic models or used where raw values are expected. See `reports/mypy.txt` for details.

## Prioritized remediation list (top 10 quick wins)
The list below targets safety (tests), maintainability, and enabling CI/CD later.

1. File: `app/routers/exercises.py` — Smell: large router functions, many untested branches, multiple statements on one line.
   - Fix: Break update handlers into clearer assignments (no inline `if`-statements on one line). Extract business logic into a service module `app/services/exercises.py`. Add unit tests for service functions and add integration tests for endpoints.
   - Priority: High

2. File: `app/routers/sessions.py` — Smell: similar to exercises router (duplicated patterns, low coverage).
   - Fix: Extract `app/services/sessions.py`, add unit + integration tests, remove duplicated code by reusing shared helpers.
   - Priority: High

3. File: `app/main.py` — Smell: duplicate/unordered imports and unused import `.models` (ruff F401/E402/F811).
   - Fix: Reorder imports to top-of-file, remove unused imports, and ensure static file mounting is done once and cleanly.
   - Priority: Medium

4. File: `app/schemas.py` — Smell: duplicate typing imports and invalid type alias usage flagged by mypy.
   - Fix: Consolidate `typing` imports at top. Define type aliases in a mypy-friendly way (use `from typing import Optional, List, Literal` at top and avoid redefining names). Consider adding `# type: ignore` where necessary or refactor Pydantic types to be clearer.
   - Priority: Medium

5. File: `app/database.py` — Smell: possible hardcoded DB path and missing centralized `get_db()` dependency.
   - Fix: Centralize engine creation and export a `get_db()` generator for FastAPI dependency injection. Load DB path via environment variable / config module (do not hardcode `rehab.db` in multiple places).
   - Priority: High

6. SQLAlchemy usage across routers — Smell: mypy shows SQLAlchemy Column objects being passed to Pydantic models (wrong use of model instances vs Column objects).
   - Fix: When constructing response schemas, use model instance attributes (`ex.name`, `ex.id`) or `vars()`/`obj.__dict__` mapping, not Column objects. Add small adapter/helper to map ORM -> Pydantic.
   - Priority: High

7. JSON serialization for fields (e.g., `schedule_dow`) — Smell: ad-hoc json.dumps / json.loads scattered in routers.
   - Fix: Move (de)serialization into model property or service layer; store canonical representation in DB and centralize conversion in schema layer.
   - Priority: Medium

8. Tests: unused imports and brittle setup — Smell: tests import `pytest` but don't use it; tests rely on package imports but currently succeed only if `PYTHONPATH=.` is set.
   - Fix: Clean test imports; add `tests/conftest.py` fixtures for `client` and `test_db` to make tests self-contained; document running tests (we used `PYTHONPATH=.` here).
   - Priority: Medium

9. Apply automatic lint fixes — Smell: many small stylistic issues reported by ruff.
   - Fix: Run `ruff --fix` (or fix manually) to resolve E701/E402/F401 where safe. Re-run tests to ensure behavior unchanged.
   - Priority: Low

10. Add health & metrics endpoints (not present) — Smell: no readiness/health check or metrics.
    - Fix: Add `/health` and `/metrics` (via `prometheus_client`) in Day 6. This is required by assignment monitoring requirements.
    - Priority: Medium (Day 6 task)

## Immediate next steps (Day 2)
1. Create a feature branch `feat/refactor-db` or continue on `feat/day1-analysis`.
2. Implement high-priority refactors:
   - Add `get_db()` in `app/database.py`
   - Extract service modules `app/services/exercises.py` and `app/services/sessions.py` containing the business logic used by routers
   - Fix SQLAlchemy -> Pydantic mapping helper
3. Run `ruff --fix` to auto-fix trivial lints, then re-run tests.
4. Add `tests/conftest.py` and begin adding unit tests for the extracted services.

## Where raw outputs live (for reviewer)
- `reports/pytest-output.txt`
- `reports/pytest-coverage-term.txt`
- `reports/coverage.xml`
- `reports/htmlcov/index.html` (open in browser for per-line coverage)
- `reports/lint-ruff.txt`
- `reports/mypy.txt`

---
If you'd like, I can implement Day 2 now: create `get_db()` and extract service functions and run the tests again. Tell me to proceed and I'll update the todo list status and make code changes in small commits.
