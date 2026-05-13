# CaveSketch — Gemini CLI Refactor & Feature Plan

> **How to use this file**
> Each section below is a self-contained Gemini CLI session.
> Start every session with:
> ```
> gemini
> > read GEMINI.md
> > read <the file(s) listed under "Read first">
> ```
> Then paste the prompt verbatim. Do **one job per session**.
> A job is done when all items in its **Done when** checklist are satisfied.

---

## Prerequisites — do once before any session

1. Read the full `app.py`, `cave_sketch/` package, and `requirements.txt` so you understand the current state.
2. Create `GEMINI.md` at the repo root (see template at the bottom of this file).
3. Install `uv` if not already present: `curl -Lf https://astral.sh/uv/install.sh | sh`

---

## Phase 0 — uv & packaging bootstrap

### Job 0a — Convert to uv-managed project

**Read first:** `requirements.txt`, root directory listing

**Prompt:**
```
Convert this project to be managed by uv.

Steps:
1. Create a `pyproject.toml` at the repo root with:
   - [project] section: name="cave-sketch", version="0.1.0", requires-python=">=3.11"
   - All dependencies from requirements.txt under [project.dependencies] with pinned versions
   - [project.optional-dependencies] dev group containing: pytest>=8, pytest-cov, ruff, mypy
   - [build-system] using hatchling
   - [tool.ruff] section enabling E, F, I rule sets, line-length=100
   - [tool.mypy] section with strict=false, ignore_missing_imports=true
2. Run `uv lock` to generate `uv.lock`
3. Run `uv sync --all-extras` to verify the environment resolves cleanly
4. Delete `requirements.txt` (its content is now in pyproject.toml)
5. Update the "Run Locally" section of README.md to use:
   `uv sync && uv run streamlit run app/app.py`
```

**Done when:**
- [x] `pyproject.toml` exists with all deps
- [x] `uv.lock` exists and is committed
- [x] `requirements.txt` is deleted
- [x] `uv run streamlit run app.py` launches the app without errors

---

## Phase 1 — Structural refactor

### Job 1a — Add typed dataclasses (models)

**Read first:** `cave_sketch/parse_dxf.py`, `cave_sketch/survey.py`

**Prompt:**
```
Create `cave_sketch/dxf/models.py` with typed dataclasses representing the domain objects used by the DXF parser and survey renderer.

Requirements:
- Infer the required fields by reading how parse_dxf.py and survey.py consume the parsed data.
- Define at minimum: SurveyPoint (id, x, y, z or depth), SurveyLine (from_id, to_id), CaveSurvey (points: list[SurveyPoint], lines: list[SurveyLine], name: str).
- Use Python dataclasses with full type annotations.
- Add a short docstring to each class.
- Do NOT import streamlit anywhere in this file.
- Create `cave_sketch/dxf/__init__.py` (empty) if it doesn't exist.
```

**Done when:**
- [x] `cave_sketch/dxf/models.py` exists
- [x] `mypy cave_sketch/dxf/models.py` passes with zero errors
- [x] No Streamlit import anywhere in the file

---

### Job 1b — Extract DXF parser

**Read first:** `cave_sketch/parse_dxf.py`, `cave_sketch/dxf/models.py` (from 1a)

**Prompt:**
```
Move and refactor the DXF parsing logic into `cave_sketch/dxf/parser.py`.

Requirements:
1. The public API must be a single function:
   `def parse_dxf(input_path: Path, output_path: Path | None = None) -> CaveSurvey`
   returning a CaveSurvey dataclass (from models.py).
2. Preserve all existing parsing logic — do not change behaviour, only restructure.
3. Add full type annotations and a module-level docstring.
4. No Streamlit imports.
5. Write `tests/test_dxf_parser.py` with at least 3 pytest tests:
   - test that a valid DXF returns a CaveSurvey with non-empty points
   - test that a missing file raises FileNotFoundError
   - test that the optional output_path writes a CSV when provided
   Use the existing sample DXF file in the repo as test fixture (copy it to `tests/fixtures/`).
6. Keep the old `cave_sketch/parse_dxf.py` but make it a thin re-export shim:
   `from cave_sketch.dxf.parser import parse_dxf  # noqa: F401`
   so existing imports in app.py don't break yet.
```

**Done when:**
- [x] `cave_sketch/dxf/parser.py` exists with typed API
- [x] `tests/test_dxf_parser.py` has ≥3 tests, all passing via `uv run pytest tests/test_dxf_parser.py`
- [x] Old import path still works (shim in place)
- [x] `ruff check cave_sketch/dxf/parser.py` clean

---

### Job 1c — Extract georeferencing layer

**Read first:** `cave_sketch/satellite_view.py`, `cave_sketch/dxf/models.py`

**Prompt:**
```
Extract the GPS georeferencing logic from cave_sketch/satellite_view.py into `cave_sketch/geo/georef.py`.

Requirements:
1. Create the module with a typed public function:
   `def georeference(survey: CaveSurvey, gps_refs: list[GpsRef]) -> list[GeoPoint]`
   where GpsRef = dataclass(station_id: str, lat: float, lon: float) and
   GeoPoint = dataclass(station_id: str, lat: float, lon: float, x: float, y: float).
   Define GpsRef and GeoPoint in `cave_sketch/geo/models.py`.
2. The georeferencing must support ≥2 reference points and use an affine transform (as the existing code does).
3. Preserve existing behaviour exactly — only restructure.
4. No Streamlit imports.
5. Create `cave_sketch/geo/__init__.py` (empty).
6. Write `tests/test_georef.py` with at least 2 tests:
   - test that 2 known GPS refs produce correctly transformed GeoPoints
   - test that <2 refs raises ValueError with a descriptive message
```

**Done when:**
- [x] `cave_sketch/geo/georef.py` and `cave_sketch/geo/models.py` exist
- [x] `uv run pytest tests/test_georef.py` passes
- [x] `mypy cave_sketch/geo/` passes
- [x] `satellite_view.py` still works (imports the new function internally)

---

### Job 1d — Extract survey renderer

**Read first:** `cave_sketch/survey.py`, `cave_sketch/dxf/models.py`

**Prompt:**
```
Move the survey rendering and PDF export logic from cave_sketch/survey.py into two focused modules:
- `cave_sketch/survey/renderer.py` — matplotlib figure generation
- `cave_sketch/survey/pdf.py` — PDF file output

Requirements:
1. Public API for renderer:
   `def render_survey(survey: CaveSurvey, config: SurveyConfig) -> matplotlib.figure.Figure`
   where SurveyConfig is a dataclass defined in `cave_sketch/survey/config.py` holding all the
   current keyword arguments (rule_length, rotation_deg, show_details, marker_zoom, text_zoom, line_width_zoom).
2. Public API for pdf:
   `def export_pdf(fig: Figure, output_path: Path) -> Path`
3. Keep `cave_sketch/survey.py` as a shim re-exporting draw_survey for backward compat.
4. No Streamlit imports in any of these files.
5. Create `cave_sketch/survey/__init__.py`.
```

**Done when:**
- [x] Three new files exist: `renderer.py`, `pdf.py`, `config.py`
- [x] `mypy cave_sketch/survey/` passes
- [x] App still runs end-to-end

---

### Job 1e — Centralise session state

**Read first:** `app.py` (full file)

**Prompt:**
```
Refactor session state management in the Streamlit app.

Steps:
1. Create `app/session.py` with:
   - A TypedDict or dataclass `AppState` documenting every session_state key and its type.
   - A single function `init_session() -> None` that initialises all keys with defaults if absent.
   - Helper getters/setters where the type would otherwise require casting.
2. Replace all scattered `if "X" not in st.session_state: st.session_state.X = ...`
   blocks in app.py with a single `init_session()` call at the top.
3. If app.py has not yet been moved to app/, do so now and update the run command in README.

Do not change any UI behaviour — only reorganise state initialisation.
```

**Done when:**
- [x] `app/session.py` exists
- [x] No `if "X" not in st.session_state` pattern anywhere outside `session.py`
- [x] App runs without errors

---

### Job 1f — Split into multi-page Streamlit app

**Read first:** `app/app.py` (or current app.py), `app/session.py`

**Prompt:**
```
Split the single-page Streamlit app into a multi-page app using Streamlit's native pages feature.

Structure to create:
  app/
    app.py              ← landing page: title, brief description, navigation hints
    pages/
      1_survey_plot.py  ← everything under "Cave Survey" section
      2_satellite_map.py ← everything under "Position Cave on Map" section
    components/
      file_upload.py    ← shared file uploader widget (used by both pages)
      gps_points.py     ← the known-points editor widget
      settings_panel.py ← survey settings sliders/inputs

Requirements:
- session state (from session.py) must be initialised on every page load; call init_session() at the top of each page file.
- No business logic in page files — they call cave_sketch library functions only.
- Each page file should be under 80 lines.
- Fix the bare `except:` clauses in JSON loading: replace with `except (json.JSONDecodeError, KeyError)`.
- Fix the st.stop() inside button logic: replace with else-branch patterns.
```

**Done when:**
- [x] `app/pages/1_survey_plot.py` and `2_satellite_map.py` exist
- [x] Each page file < 80 lines
- [x] No bare `except:` remaining
- [x] No `st.stop()` inside button handlers
- [x] Both features work end-to-end

---

## Phase 2 — CI & tooling

### Job 2a — GitHub Actions CI

**Read first:** `pyproject.toml` (from 0a)

**Prompt:**
```
Create `.github/workflows/ci.yml` for this project.

Requirements:
1. Trigger on: push and pull_request to main branch.
2. Single job "test" running on ubuntu-latest, Python 3.11.
3. Steps:
   a. checkout
   b. install uv (`pip install uv`)
   c. `uv sync --all-extras`
   d. `uv run ruff check .`
   e. `uv run mypy cave_sketch/`
   f. `uv run pytest tests/ --cov=cave_sketch --cov-report=term-missing`
4. Cache the uv virtual environment using actions/cache on the uv.lock hash.
5. Add a README badge for the workflow status.
```

**Done when:**
- [x] `.github/workflows/ci.yml` exists and is valid YAML
- [x] Workflow passes on a clean push (check Actions tab)
- [x] README has a CI badge

---

### Job 2b — pre-commit hooks

**Read first:** `pyproject.toml`

**Prompt:**
```
Add pre-commit configuration to the project.

1. Create `.pre-commit-config.yaml` with hooks:
   - ruff (lint + autofix)
   - ruff-format (formatter)
   - mypy on cave_sketch/ only
   - check for trailing whitespace and end-of-file newlines
2. Add `pre-commit` to the dev dependencies in pyproject.toml.
3. Run `uv run pre-commit run --all-files` and fix any issues it reports.
4. Add setup instructions to the developer section of README.md:
   `uv run pre-commit install`
```

**Done when:**
- [ ] `.pre-commit-config.yaml` exists
- [ ] `uv run pre-commit run --all-files` exits 0
- [ ] README updated

---

## Phase 3 — New features

> Run these only after Phase 1 and Phase 2 are complete.

### Job 3a — KML export

**Read first:** `create_kml.py` (root), `cave_sketch/geo/georef.py`, `cave_sketch/geo/models.py`

**Prompt:**
```
Implement KML export as a proper library module.

1. Create `cave_sketch/geo/kml.py`:
   - Public function: `def export_kml(geo_points: list[GeoPoint], name: str, output_path: Path) -> Path`
   - Use the simplekml library (add it to pyproject.toml dependencies) or the stdlib xml module.
   - Migrate all logic from the root-level create_kml.py.
2. Add a "Download KML" button to `app/pages/2_satellite_map.py` alongside the existing HTML download.
3. Write `tests/test_kml.py` with at least 1 test: that exporting a known list of GeoPoints produces
   a valid KML file containing those coordinates.
4. Delete the root-level `create_kml.py` once the new module is verified.
```

**Done when:**
- [ ] `cave_sketch/geo/kml.py` exists, typed, tested
- [ ] KML download button works in the app
- [ ] Root `create_kml.py` deleted
- [ ] `uv run pytest tests/test_kml.py` passes

---

### Job 3b — Survey merge

**Read first:** `merge_surveys.py` (root), `cave_sketch/dxf/models.py`, `app/pages/2_satellite_map.py`

**Prompt:**
```
Implement survey merging as a proper library module.

1. Create `cave_sketch/utils/merge.py`:
   - Public function: `def merge_surveys(surveys: list[CaveSurvey]) -> CaveSurvey`
   - Migrates logic from root-level merge_surveys.py.
   - Handles duplicate station IDs by prefixing with survey name.
2. The satellite map page already allows uploading JSON maps. Wire this up so uploaded surveys
   are deserialised to CaveSurvey objects and merged before georeferencing.
3. Add `cave_sketch/utils/__init__.py`.
4. Write `tests/test_merge.py`: test that merging 2 surveys with overlapping station IDs produces
   a survey where all stations are present and IDs are unique.
5. Delete root-level `merge_surveys.py`.
```

**Done when:**
- [ ] `cave_sketch/utils/merge.py` exists, typed, tested
- [ ] Merge works end-to-end in the app
- [ ] Root `merge_surveys.py` deleted

---

### Job 3c — Temp file cleanup

**Read first:** `app/session.py`, `app/app.py`

**Prompt:**
```
Fix the temp directory leak in the Streamlit app.

Currently, each session creates a unique temp directory under /tmp that is never deleted.

1. Add a `cleanup_session() -> None` function to `app/session.py` that removes the session's
   files_dir using shutil.rmtree(ignore_errors=True).
2. Register it with Streamlit's `st.cache_resource` teardown or use an atexit handler so it
   runs when the session ends.
3. Add a "🗑️ Clear session files" button in the sidebar visible on all pages that calls cleanup
   and then st.rerun().
4. Document the temp dir strategy in a comment in session.py.
```

**Done when:**
- [ ] Temp dirs are cleaned up on session end
- [ ] Clear button works manually
- [ ] No orphaned dirs accumulate across test runs

---

### Job 3d — 3D OBJ export

**Read first:** `cave_mesh.obj` (root, for reference output format), `cave_sketch/survey/renderer.py`, `cave_sketch/dxf/models.py`

**Prompt:**
```
Add 3D OBJ export from a CaveSurvey.

1. Create `cave_sketch/survey/obj_export.py`:
   - Public function: `def export_obj(survey: CaveSurvey, output_path: Path) -> Path`
   - Represent each survey station as a vertex; each survey line as an edge (l statement in OBJ).
   - Use the existing cave_mesh.obj in the repo root as a reference for expected output format.
2. Add a "Download OBJ" button to the survey plot page.
3. Write `tests/test_obj_export.py`: test that exporting a minimal CaveSurvey produces a valid
   OBJ file with the correct number of vertices and edges.
4. Move cave_mesh.obj to tests/fixtures/ as a reference artifact.
```

**Done when:**
- [ ] `cave_sketch/survey/obj_export.py` exists, typed, tested
- [ ] OBJ download button works in the app
- [ ] `cave_mesh.obj` moved to `tests/fixtures/`

---

## GEMINI.md template

Copy this file to the repo root as `GEMINI.md`:

```markdown
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
- `uv run ruff check . --fix` before finishing any task
- `uv run mypy cave_sketch/` must pass
- No bare `except:` — always catch specific exception types
- No `st.stop()` inside button handlers — use else-branch patterns

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
5. Implement, then run: `uv run ruff check . --fix && uv run mypy cave_sketch/ && uv run pytest`
6. After every meaningful code change, append an entry to `DEVLOG.md`:

## [YYYY-MM-DD HH:MM] <phase> — <action>
**Files:** <list of files created or modified, one per line>
**Deviations from spec:** <what and why, or "None">
**Assumptions:** <anything not explicit in the spec, or "None">
**Next session notes:** <what the next session must know, or "None">
```
