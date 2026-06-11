# Spec: Dynamic Download Filenames from Survey Name

## Overview

Currently, all downloaded files use hardcoded filenames (`survey.pdf`, `cave_map.html`, `cave_map.json`, `cave_map.kml`). This track changes every download button to use the **Survey Name** entered by the user as the base filename, with proper sanitization for filesystem safety.

## Functional Requirements

### FR-1: Store survey name in session state
- The survey name entered via `survey_name_component()` must be persisted in `st.session_state` so it is accessible from any page.
- Default value: `"MySurvey"` (existing default, unchanged).
- Add `survey_name` to the `AppState` TypedDict in `session.py`.

### FR-2: Sanitize survey name for filenames
- Create a utility function `sanitize_filename(name: str) -> str` in the `cave_sketch` library layer (e.g. `cave_sketch/utils/filename.py`).
- Sanitization rules:
  - Strip leading/trailing whitespace.
  - Replace spaces and sequences of non-alphanumeric characters (except hyphens and underscores) with a single underscore.
  - Convert to lowercase.
  - If the result is empty after sanitization, fall back to `"my_survey"`.
- Example: `"My Cave Survey!"` → `"my_cave_survey"`.

### FR-3: Use sanitized survey name in all download buttons
- **Survey Plot page** (`1_survey_plot.py`): Change `file_name="survey.pdf"` → `file_name=f"{sanitized_name}.pdf"`.
- **Satellite Map page** (`2_satellite_map.py`): Change all three download buttons:
  - `cave_map.html` → `{sanitized_name}.html`
  - `cave_map.json` → `{sanitized_name}.json`
  - `cave_map.kml` → `{sanitized_name}.kml`

### FR-4: Survey name editable on both pages
- The `survey_name_component()` widget appears on both the Survey Plot and Satellite Map pages.
- Both instances read from and write to the same `st.session_state.survey_name` key, so edits on one page are reflected on the other.

## Non-Functional Requirements

- The `sanitize_filename()` function must live in the `cave_sketch/` library layer (no Streamlit imports).
- Full type annotations on the new function.
- Unit tests for `sanitize_filename()` covering normal input, special characters, empty/whitespace-only input, and the fallback.

## Acceptance Criteria

1. Downloading a PDF when Survey Name is `"My Cave"` produces a file named `my_cave.pdf`.
2. Downloading HTML/JSON/KML when Survey Name is `"Test Survey!"` produces `test_survey.html`, `test_survey.json`, `test_survey.kml`.
3. If the user clears the Survey Name field entirely, downloads fall back to `my_survey.*`.
4. Changing the survey name on the Satellite Map page is reflected on the Survey Plot page and vice versa.
5. `uv run ruff check .`, `uv run mypy cave_sketch/`, and `uv run pytest` all pass.

## Out of Scope

- Renaming internal temporary files (only download button `file_name` parameters change).
- Changing the `map_name` parameter passed to `draw_map()` (remains `"Current Cave"` for now).
