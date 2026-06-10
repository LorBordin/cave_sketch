# Implementation Plan: Ensure Station ID Visibility

## Phase 1: Implement Z-Order and Fixed-Offset Placement for Station IDs
- [x] Task: Write failing tests for station ID z-order and offset [34ab652]
    - [x] Create `tests/test_survey_plot.py` with tests that render a minimal survey figure and inspect the matplotlib text artists:
        - Verify each station ID text artist has `get_zorder() >= 10`.
        - Verify each station ID text artist's position is offset from the station marker coordinates (i.e., `x_text != x_station` or `y_text != y_station`).
- [ ] Task: Implement Z-Order and fixed-offset fixes
    - [ ] In `cave_sketch/survey/graphics/survey_plot.py` (line ~67), update the `ax.text()` call for station IDs:
        - Set `zorder=10` (above the scatter marker's `zorder=5`).
        - Apply a small data-unit offset to `x` and `y` so the label is nudged away from the marker center (e.g., `x + offset, y + offset` where `offset` is proportional to `text_size` or a fixed fraction of the axis scale).
- [ ] Task: Conductor - User Manual Verification 'Implement Z-Order and Fixed-Offset Placement for Station IDs' (Protocol in workflow.md)