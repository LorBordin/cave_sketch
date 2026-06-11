# Plan: Dynamic Download Filenames from Survey Name

## Phase 1: Sanitize Filename Utility [checkpoint: 9ad0962]

- [x] Task: Write tests for `sanitize_filename()` (2185051)
    - [x] Create `tests/test_sanitize_filename.py`
    - [x] Test normal input (e.g. `"My Cave"` → `"my_cave"`)
    - [x] Test special characters (e.g. `"Test!@#Survey"` → `"test_survey"`)
    - [x] Test leading/trailing whitespace is stripped
    - [x] Test multiple consecutive spaces/special chars collapse to single underscore
    - [x] Test empty string falls back to `"my_survey"`
    - [x] Test whitespace-only input falls back to `"my_survey"`
    - [x] Test hyphens and underscores are preserved
    - [x] Run tests and confirm they fail (Red phase)

- [x] Task: Implement `sanitize_filename()` (fd54bf1)
    - [x] Create `cave_sketch/utils/filename.py` with the `sanitize_filename(name: str) -> str` function
    - [x] Ensure no Streamlit imports in the library layer
    - [x] Full type annotations
    - [x] Run tests and confirm they pass (Green phase)

- [x] Task: Conductor - User Manual Verification 'Phase 1: Sanitize Filename Utility' (Protocol in workflow.md)

## Phase 2: Session State & UI Integration

- [ ] Task: Add `survey_name` to session state
    - [ ] Add `survey_name: str` to `AppState` TypedDict in `app/session.py`
    - [ ] Add `"survey_name": "MySurvey"` to the defaults dict in `init_session()`

- [ ] Task: Update `survey_name_component()` to use session state
    - [ ] Modify `app/components/file_upload.py` so `survey_name_component()` reads from and writes to `st.session_state.survey_name`
    - [ ] Use `st.text_input` with `key="survey_name"` to auto-sync with session state

- [ ] Task: Add survey name component to Satellite Map page
    - [ ] Import `survey_name_component` in `app/pages/2_satellite_map.py`
    - [ ] Place the widget in an appropriate location on the page

- [ ] Task: Update download buttons to use sanitized survey name
    - [ ] In `app/pages/1_survey_plot.py`: change `file_name="survey.pdf"` to use sanitized survey name
    - [ ] In `app/pages/2_satellite_map.py`: change all three `file_name="cave_map.*"` to use sanitized survey name
    - [ ] Import `sanitize_filename` from `cave_sketch.utils.filename` in both pages

- [ ] Task: Conductor - User Manual Verification 'Phase 2: Session State & UI Integration' (Protocol in workflow.md)
