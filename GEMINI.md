# CaveSketch — project context for Gemini CLI

## What this is
A Streamlit app for cavers. Takes TopoDroid DXF exports (.dxf), generates:
- PDF cave survey plots (plan + section) with configurable scale and rotation
- Satellite HTML maps overlaying the cave on GPS-georeferenced satellite imagery
- KML exports for Google Earth
- JSON cave map format for merging multiple surveys

Users are field researchers, often on mobile with limited connectivity.

## Project management
- Managed with **uv** (`uv sync`, `uv run`, `uv add`)
- Do NOT use pip directly; always use uv
- Lock file: uv.lock (commit it)

## Architecture
- `cave_sketch/` — pure Python library. **Zero Streamlit imports allowed here.**
  - `dxf/` — DXF parsing, domain models
  - `survey/` — matplotlib rendering, PDF/OBJ export
  - `geo/` — georeferencing, HTML map, KML export
  - `utils/` — merge, file I/O helpers
- `app/` — Streamlit glue layer only. Pages call library functions; no business logic here.
  - `pages/` — multi-page Streamlit pages
  - `components/` — reusable UI widgets
  - `session.py` — all session_state management
- `tests/` — pytest, run with `uv run pytest`
- `tests/fixtures/` — sample DXF, OBJ, and JSON files for tests

## Code standards
- Python 3.11+, full type annotations on all public functions
- **Mandatory:** `uv run ruff check .` must pass without errors before finishing any task. Use `--fix` to resolve auto-fixable issues, but manually fix the rest.
- `uv run mypy cave_sketch/` must pass.
- No bare `except:` — always catch specific exception types.
- No `st.stop()` inside button handlers — use else-branch patterns.

## Mandatory Verification
Before claiming any task is complete or reporting success, you MUST execute and confirm the following:
1. `uv run ruff check .` (Must output "All checks passed!")
2. `uv run mypy cave_sketch/` (Must output "Success: no issues found")
3. `uv run pytest` (All tests must pass)

Failure to run these and verify their success is a violation of project standards.

## Key domain knowledge
- DXF files come from TopoDroid and have a specific layer naming convention (check parse_dxf.py)
- Georeferencing uses an affine transform computed from ≥2 known station→GPS pairs
- PDF output must be print-ready at 1:N scale with a drawn scale bar
- Survey stations have alphanumeric IDs matching TopoDroid's naming

## Before implementing any task
1. Read this file
2. Read the specific source files listed under "Read first" in `specs/code_refactoring_plan.md`
3. Read `DEVLOG.md`, it contains decisions from previous sessions that override the spec where they conflict.
4. Check `tests/` for relevant existing tests
5. Implement, then perform **Mandatory Verification** as described above.
6. After every meaningful code change, append an entry to the relevant DEVLOG
   (format below). **Two logs:** the root `DEVLOG.md` covers the Python project
   (`cave_sketch` core + Streamlit web app); the Android mobile app logs to
   `android/DEVLOG.md`. See `docs/mobile-app/` for the mobile initiative.

## [YYYY-MM-DD HH:MM] <phase> — <action>
**Files:** <list of files created or modified, one per line>
**Deviations from spec:** <what and why, or "None">
**Assumptions:** <anything not explicit in the spec, or "None">
**Next session notes:** <what the next session must know, or "None">
