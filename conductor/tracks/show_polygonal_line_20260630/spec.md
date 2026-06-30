# Spec: Show Polygonal Line Toggle

## Overview

Add a new "Show Polygonal Line" checkbox to the survey plot rendering options. When unchecked, the polygonal line (the centerline connecting survey stations via measured shots) is hidden from the rendered survey plot. This toggle applies to both plan and section views.

**Cascading behavior:** When the polygonal line is hidden, station markers are also automatically hidden, regardless of the "Show Station Markers" toggle state. When the polygonal line is shown, station marker visibility returns to being controlled by its own independent toggle.

## Functional Requirements

### FR-1: Backend — RenderConfig Extension
- Add a new field `show_centerline: bool = True` to the `SurveyConfig` dataclass in `cave_sketch/survey/config.py`.
- Default value is `True` (polygonal line visible by default, preserving existing behavior).

### FR-2: Backend — Conditional Rendering
- In the rendering pipeline, gate the drawing of station-type lines (the polygonal/centerline) with `show_centerline`.
- When `show_centerline` is `False`, also skip drawing station markers regardless of `show_details`.
- When `show_centerline` is `True`, station markers respect `show_details` as before.

### FR-3: Streamlit Webapp — Session State
- Add `show_centerline: True` to the session state defaults in `app/session.py` (if applicable).
- Map `show_centerline` through the config dict to `draw_survey()`.

### FR-4: Streamlit Webapp — UI Checkbox
- Add a "Show Polygonal Line" checkbox in `app/components/settings_panel.py`.
- Place it **above** the existing "Show Station Markers" checkbox (since it cascades over it).
- When unchecked, the "Show Station Markers" checkbox should be visually disabled (greyed out) to indicate it has no effect.

### FR-5: Android App — Kotlin UI
- Add a "Show Polygonal Line" toggle in `SettingsForm.kt`.
- Place it above the existing "Show station markers" toggle.
- When disabled, the "Show station markers" toggle should be visually disabled.
- Wire the new state through `SurveyPlotViewModel.kt`.

### FR-6: Android App — Python Bridge
- Pass the `show_centerline` option in the JSON dict from `SurveyInputs.toJson()` → `survey_bridge.py`.
- Map `show_centerline` to `SurveyConfig` in `survey_bridge.py`.

## Non-Functional Requirements

- **Backward compatibility:** Existing behavior is preserved when the toggle is checked (default state).
- **Type safety:** Full type annotations on all new/modified public functions.
- **Linting:** `ruff check .` and `mypy cave_sketch/` must pass.

## Acceptance Criteria

1. With "Show Polygonal Line" checked (default): survey renders identically to current behavior.
2. With "Show Polygonal Line" unchecked: no shot lines are drawn in either plan or section view.
3. With "Show Polygonal Line" unchecked: station markers are hidden regardless of their own toggle state.
4. With "Show Polygonal Line" unchecked: the "Show Station Markers" control is visually disabled in both Streamlit and Android UIs.
5. With "Show Polygonal Line" re-checked: station markers respect their own toggle again.
6. All existing tests continue to pass.
7. New unit tests cover the conditional rendering logic.

## Out of Scope

- Changing the visual style (color, thickness) of the polygonal line.
- Adding per-view (plan vs section) independent toggles.
- Modifying KML/HTML map rendering (georeferenced views are unaffected).
