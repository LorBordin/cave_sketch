# Plan: Show Polygonal Line Toggle

## Phase 1: Backend — Config & Rendering Logic [checkpoint: b8b32f1]

- [x] Task: Write Tests — `show_centerline` config field and conditional rendering (a7f7663)
    - [x] Test that `SurveyConfig` has a `show_centerline` field defaulting to `True`
    - [x] Test that when `show_centerline=True`, station-type lines are included in extracted features
    - [x] Test that when `show_centerline=False`, station-type lines are excluded from extracted features
    - [x] Test that when `show_centerline=False`, station markers (`show_details`) are also suppressed
    - [x] Test that when `show_centerline=True` and `show_details=True`, station markers are rendered
    - [x] Test that when `show_centerline=True` and `show_details=False`, station markers are hidden but centerline is drawn

- [x] Task: Implement — Add `show_centerline` field to `SurveyConfig` dataclass (a7f7663)
    - [x] Add `show_centerline: bool = True` to `SurveyConfig` in `cave_sketch/survey/config.py`

- [x] Task: Implement — Gate polygonal line and station markers in the rendering pipeline (a7f7663)
    - [x] Pass `show_centerline` through `renderer.py` config dict
    - [x] In `cave_sketch/features/render_features.py`, skip station-type line extraction when `show_centerline=False`
    - [x] In `cave_sketch/survey/graphics/survey_plot.py`, suppress station markers when `show_centerline=False` (cascading)

- [x] Task: Conductor - User Manual Verification 'Phase 1: Backend — Config & Rendering Logic' (Protocol in workflow.md) (b8b32f1)

## Phase 2: Streamlit Webapp UI

- [ ] Task: Implement — Add `show_centerline` to Streamlit session state and settings panel
    - [ ] Add `show_centerline` default to session state in `app/session.py` (if used)
    - [ ] Add "Show Polygonal Line" checkbox in `app/components/settings_panel.py`, placed above "Show Station Markers"
    - [ ] When "Show Polygonal Line" is unchecked, disable the "Show Station Markers" checkbox visually
    - [ ] Map `show_centerline` through to `draw_survey()` config dict in `app/pages/1_survey_plot.py`

- [ ] Task: Conductor - User Manual Verification 'Phase 2: Streamlit Webapp UI' (Protocol in workflow.md)

## Phase 3: Android App UI & Bridge

- [ ] Task: Implement — Add `showCenterline` to Android data model and Python bridge
    - [ ] Add `showCenterline: Boolean = true` to `SurveyInputs` data class in `SurveyPlotViewModel.kt`
    - [ ] Add JSON serialization for `show_centerline` in `SurveyInputs.toJson()`
    - [ ] Map `show_centerline` in `survey_bridge.py` config dict

- [ ] Task: Implement — Add "Show Polygonal Line" toggle to Android settings UI
    - [ ] Add checkbox/toggle in `SettingsForm.kt`, placed above "Show station markers"
    - [ ] When unchecked, visually disable the "Show station markers" checkbox
    - [ ] Wire state through `SurveyPlotScreen.kt`

- [ ] Task: Conductor - User Manual Verification 'Phase 3: Android App UI & Bridge' (Protocol in workflow.md)
