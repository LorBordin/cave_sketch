# Implementation Plan: Survey Grid Overlay

## Phase 1: Grid Rendering Module

- [x] Task: Write tests for `_add_grid` (ba50a25)
    - [x] Create `tests/test_grid.py`
    - [x] Test that `_add_grid` draws horizontal and vertical lines on an Axes
    - [x] Test that grid spacing equals `rule_length / 2`
    - [x] Test that grid lines are aligned to clean multiples of the spacing (e.g., 0, 10, 20 for spacing=10)
    - [x] Test that grid lines use light gray dotted style (`color='lightgray'`, `linestyle=':'`)
    - [x] Test that grid lines have lowest z-order (zorder=0)
    - [x] Test that grid covers the full data extent
- [x] Task: Implement `_add_grid` in `cave_sketch/survey/graphics/grid.py` (6c54f47)
    - [x] Create new module `cave_sketch/survey/graphics/grid.py`
    - [x] Implement `_add_grid(ax, x_min, x_max, y_min, y_max, grid_spacing)` function
    - [x] Compute grid line positions snapped to multiples of `grid_spacing`
    - [x] Draw horizontal and vertical dotted light-gray lines at lowest z-order
- [x] Task: Conductor - User Manual Verification 'Phase 1: Grid Rendering Module' (Protocol in workflow.md)

## Phase 2: Integration into Survey Plot Pipeline

- [ ] Task: Write tests for grid integration in `create_survey`
    - [ ] Add tests in `tests/test_grid.py` (or `tests/test_survey_plot.py`) verifying that `create_survey` calls `_add_grid` when `show_grid=True`
    - [ ] Test that grid is NOT drawn when `show_grid=False`
    - [ ] Test that grid spacing adapts to different `rule_length` values
- [ ] Task: Add `show_grid` to `SurveyConfig` and wire through the pipeline
    - [ ] Add `show_grid: bool = True` field to `SurveyConfig` in `cave_sketch/survey/config.py`
    - [ ] Pass `show_grid` from `SurveyConfig` through `render_survey()` into `create_survey()` via `config_dict`
    - [ ] Call `_add_grid()` in `create_survey()` after computing data bbox and before rendering features
    - [ ] Grid spacing = `rule_length / 2`
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Integration into Survey Plot Pipeline' (Protocol in workflow.md)

## Phase 3: Streamlit UI Toggle

- [ ] Task: Write tests for UI toggle state
    - [ ] Add test verifying `show_grid` default is `True` in session state
    - [ ] Add test verifying `show_grid` is passed to `SurveyConfig`
- [ ] Task: Add "Show grid" checkbox to the Streamlit survey settings panel
    - [ ] Add `show_grid` to `app/session.py` session state initialization
    - [ ] Add a `st.checkbox("Show grid", ...)` in `app/pages/1_survey_plot.py` settings area
    - [ ] Pass the value through to `SurveyConfig` when constructing the config for rendering
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Streamlit UI Toggle' (Protocol in workflow.md)
