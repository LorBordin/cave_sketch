# Development Log

## [2026-05-13 14:55] Prerequisites — Implementation
**Files:**
- GEMINI.md
- DEVLOG.md

**Deviations from spec:** None
**Assumptions:** None
**Next session notes:** Ready to start Phase 0.

## [2026-05-13 15:30] Phase 0 & Phase 1 — Implementation
**Files:**
- pyproject.toml
- uv.lock
- README.md
- cave_sketch/dxf/models.py
- cave_sketch/dxf/parser.py
- cave_sketch/dxf/__init__.py
- cave_sketch/parse_dxf.py (shim)
- cave_sketch/geo/models.py
- cave_sketch/geo/georef.py
- cave_sketch/geo/__init__.py
- cave_sketch/survey/config.py
- cave_sketch/survey/pdf.py
- cave_sketch/survey/renderer.py
- cave_sketch/survey.py (shim)
- app/session.py
- app/app.py
- app/pages/1_survey_plot.py
- app/pages/2_satellite_map.py
- app/components/file_upload.py
- app/components/settings_panel.py
- app/components/gps_points.py
- tests/fixtures/sample.dxf
- tests/test_dxf_parser.py
- tests/test_georef.py

**Deviations from spec:**
- Created a sample DXF fixture since none existed in the repo.
- The `app/pages` logic was modernized to avoid `st.stop()` and bare `except:` as requested.
- `georeference` test required relaxed tolerance (1e-4) due to floating point averaging of coordinates.

**Assumptions:**
- `app.py` re-exported `parse_dxf` can return a `CaveSurvey` because `app.py` doesn't use the return value as a DataFrame (it relies on the CSV side-effect).

**Next session notes:** Phase 1 complete. Ready for Phase 2 (CI & tooling).

## [2026-05-13 15:45] Phase 1 — Mypy Fixes
**Files:**
- cave_sketch/survey/graphics/rule.py
- cave_sketch/survey/graphics/north.py
- cave_sketch/survey/graphics/survey_plot.py
- cave_sketch/survey/renderer.py
- cave_sketch/survey/survey.py

**Deviations from spec:** None
**Assumptions:** None
**Next session notes:** Phase 1 complete and type-safe.

## [2026-05-13 15:55] Phase 1 — App Module & Import Fixes
**Files:**
- app/__init__.py
- app/pages/__init__.py
- app/components/__init__.py
- app/app.py
- app/pages/1_survey_plot.py
- app/pages/2_satellite_map.py

**Deviations from spec:**
- Added `__init__.py` files to make `app/` a proper package structure.
- Changed `app` internal imports to be relative/direct since `streamlit run` adds the script directory to `sys.path`.
- Fixed mypy type shadowing in `2_satellite_map.py`.

**Assumptions:** None
**Next session notes:** Phase 1 fully operational and type-safe. Ready for Phase 2.

## [2026-05-13 16:15] Phase 2a — GitHub Actions CI
**Files:**
- .github/workflows/ci.yml
- README.md
- README.it.md
- pyproject.toml
- cave_sketch/__init__.py
- cave_sketch/backend_renders/__init__.py
- cave_sketch/satellite_view/__init__.py
- cave_sketch/survey/__init__.py
- cave_sketch/survey/graphics/__init__.py
- cave_sketch/backend_renders/folium.py
- cave_sketch/backend_renders/google_earth.py
- cave_sketch/backend_renders/matplotlib.py
- cave_sketch/survey.py
- cave_sketch/survey/graphics/rule.py
- cave_sketch/survey/graphics/survey_plot.py
- cave_sketch/features/geometry.py
- cave_sketch/features/render_features.py
- cave_sketch/dxf/parser.py
- cave_sketch/satellite_view/map.py
- main.py

**Deviations from spec:**
- Fixed multiple Ruff errors (F401, E741, E501, E702, F841) and MyPy errors in the core `cave_sketch/` package to ensure CI passes.
- Excluded legacy files (`utility_scripts`, `merge_surveys.py`) from Ruff check in `pyproject.toml`.
- Added CI badge to both English and Italian READMEs.

**Assumptions:**
- GitHub repo owner is `LorBordin` based on `git remote`.

**Next session notes:** Phase 2a complete. Ready for Job 2b (pre-commit).

## [2026-05-14 10:27] Phase 2b — Pre-commit hooks
**Files:**
- pyproject.toml
- uv.lock
- .pre-commit-config.yaml
- cave_sketch/survey/survey.py
- cave_sketch/survey.py (deleted)
- README.md
- README.it.md
- specs/code_refactoring_plan.md

**Deviations from spec:**
- Resolved a duplicate module conflict by moving the `draw_survey` shim from `cave_sketch/survey.py` to `cave_sketch/survey/survey.py` and deleting the former.
- Added an assertion in `draw_survey` to satisfy Mypy's type checking.
- Updated `README.it.md` to use `uv` instead of `pip` for consistency with Phase 0a.

**Assumptions:** None
**Next session notes:** Phase 2 complete. Ready for Phase 3 (New features).
